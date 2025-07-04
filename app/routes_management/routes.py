from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from app import db
from app.models import TechnologicalRoute, Operation, User, RouteVersion, Archive
from app.routes_management import bp
from app.utils import require_permission, log_audit_event, validate_route_data
from sqlalchemy.exc import IntegrityError
from datetime import datetime

@bp.route('/api/routes', methods=['GET'])
@jwt_required()
@require_permission('routes:read')
def get_routes():
    """Получить список технологических маршрутов"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        
        query = TechnologicalRoute.query
        
        # Фильтры
        if status:
            query = query.filter(TechnologicalRoute.status == status)
        
        if search:
            query = query.filter(
                TechnologicalRoute.name.ilike(f'%{search}%') |
                TechnologicalRoute.route_number.ilike(f'%{search}%')
            )
        
        # Пагинация
        routes = query.order_by(TechnologicalRoute.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        log_audit_event('routes_list_viewed', 'Просмотр списка технологических маршрутов', True)
        
        return jsonify({
            'data': [route.to_dict() for route in routes.items],
            'pagination': {
                'total': routes.total,
                'pages': routes.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': routes.has_next,
                'has_prev': routes.has_prev
            }
        })
        
    except Exception as e:
        log_audit_event('routes_list_error', f'Ошибка при получении списка маршрутов: {str(e)}', False)
        return jsonify({'error': 'Ошибка при получении списка маршрутов'}), 500

@bp.route('/api/routes', methods=['POST'])
@jwt_required()
@require_permission('routes:create')
def create_route():
    """Создать новый технологический маршрут"""
    try:
        data = request.get_json()
        
        # Комплексная валидация и санитизация
        try:
            data = validate_route_data(data)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        current_user_id = get_jwt_identity()
        
        # Создание маршрута
        route = TechnologicalRoute(
            name=data['name'],
            route_number=data['route_number'],
            created_by=current_user_id,
            description=data.get('description')
        )
        
        # Дополнительные параметры
        if 'status' in data:
            route.status = data['status']
        if 'route_data' in data:
            route.route_data = json.dumps(data['route_data'])
        if 'estimated_duration' in data:
            route.estimated_duration = data['estimated_duration']
        if 'complexity_level' in data:
            route.complexity_level = data['complexity_level']
        
        db.session.add(route)
        db.session.commit()
        
        # Создать первую версию
        route.create_version('Первоначальная версия', current_user_id)
        db.session.commit()
        
        log_audit_event('route_created', f'Создан технологический маршрут: {route.name}', True)
        
        return jsonify(route.to_dict()), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Маршрут с таким номером уже существует'}), 409
    except Exception as e:
        db.session.rollback()
        log_audit_event('route_creation_error', f'Ошибка при создании маршрута: {str(e)}', False)
        return jsonify({'error': 'Ошибка при создании маршрута'}), 500

@bp.route('/api/routes/<int:route_id>', methods=['GET'])
@jwt_required()
@require_permission('routes:read')
def get_route(route_id):
    """Получить технологический маршрут по ID"""
    try:
        route = TechnologicalRoute.query.get(route_id)
        if not route:
            return jsonify({'error': 'Маршрут не найден'}), 404
        
        log_audit_event('route_viewed', f'Просмотр маршрута: {route.name}', True)
        
        return jsonify(route.to_dict())
        
    except Exception as e:
        log_audit_event('route_view_error', f'Ошибка при получении маршрута {route_id}: {str(e)}', False)
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@bp.route('/api/routes/<int:route_id>', methods=['PUT'])
@jwt_required()
@require_permission('routes:update')
def update_route(route_id):
    """Обновить технологический маршрут"""
    try:
        route = TechnologicalRoute.query.get(route_id)
        if not route:
            return jsonify({'error': 'Маршрут не найден'}), 404
        data = request.get_json()
        
        # Проверка версии для контроля конкурентности
        if 'version' in data and data['version'] != route.version:
            return jsonify({
                'error': 'Конфликт версий. Данные были изменены другим пользователем. Обновите страницу.',
                'current_version': route.version,
                'provided_version': data['version']
            }), 409
        
        current_user_id = get_jwt_identity()
        
        # Создать версию перед изменением
        route.create_version('Автосохранение перед изменением', current_user_id)
        
        # Валидация данных обновления
        try:
            data = validate_route_data(data)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Обновление полей
        if 'name' in data:
            route.name = data['name']
        if 'description' in data:
            route.description = data['description']
        if 'status' in data:
            route.status = data['status']
        if 'route_data' in data:
            route.route_data = json.dumps(data['route_data'])
        if 'estimated_duration' in data:
            route.estimated_duration = data['estimated_duration']
        if 'complexity_level' in data:
            route.complexity_level = data['complexity_level']
        
        route.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit_event('route_updated', f'Обновлен технологический маршрут: {route.name}', True)
        
        return jsonify(route.to_dict())
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('route_update_error', f'Ошибка при обновлении маршрута {route_id}: {str(e)}', False)
        return jsonify({'error': 'Ошибка при обновлении маршрута'}), 500

@bp.route('/api/routes/<int:route_id>', methods=['DELETE'])
@jwt_required()
@require_permission('routes:delete')
def delete_route(route_id):
    """Удалить технологический маршрут с архивированием"""
    try:
        route = TechnologicalRoute.query.get_or_404(route_id)
        current_user_id = get_jwt_identity()
        
        # Архивирование перед удалением
        archive_data = route.to_dict()
        archive_data['versions'] = [v.to_dict() for v in route.versions]
        
        archive = Archive(
            entity_type='route',
            entity_id=route.id,
            entity_data=json.dumps(archive_data, ensure_ascii=False),
            archived_by=current_user_id,
            reason='deleted',
            notes=f'Маршрут удален: {route.name}'
        )
        
        db.session.add(archive)
        
        # Удаление маршрута (версии удалятся каскадно)
        route_name = route.name
        db.session.delete(route)
        db.session.commit()
        
        log_audit_event('route_deleted', f'Удален технологический маршрут: {route_name}', True)
        
        return jsonify({'message': 'Маршрут успешно удален и заархивирован'})
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('route_deletion_error', f'Ошибка при удалении маршрута {route_id}: {str(e)}', False)
        return jsonify({'error': 'Ошибка при удалении маршрута'}), 500

@bp.route('/api/routes/<int:route_id>/operations', methods=['GET'])
@jwt_required()
@require_permission('routes:read')
def get_route_operations(route_id):
    """Получить операции маршрута"""
    try:
        route = TechnologicalRoute.query.get_or_404(route_id)
        
        return jsonify({
            'operations': [op.to_dict() for op in route.operations],
            'route_info': {
                'id': route.id,
                'name': route.name,
                'route_number': route.route_number
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении операций маршрута'}), 500

@bp.route('/api/routes/<int:route_id>/operations', methods=['POST'])
@jwt_required()
@require_permission('routes:update')
def add_route_operation(route_id):
    """Добавить операцию к маршруту"""
    try:
        route = TechnologicalRoute.query.get_or_404(route_id)
        data = request.get_json()
        
        operation_id = data.get('operation_id')
        if not operation_id:
            return jsonify({'error': 'ID операции обязателен'}), 400
        
        operation = Operation.query.get_or_404(operation_id)
        
        # Проверить, что операция еще не добавлена
        if operation in route.operations:
            return jsonify({'error': 'Операция уже добавлена к маршруту'}), 409
        
        route.operations.append(operation)
        db.session.commit()
        
        log_audit_event('route_operation_added', f'Добавлена операция {operation.name} к маршруту {route.name}', True)
        
        return jsonify({
            'message': 'Операция добавлена к маршруту',
            'operation': operation.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при добавлении операции'}), 500

@bp.route('/api/routes/<int:route_id>/versions', methods=['GET'])
@jwt_required()
@require_permission('routes:read')
def get_route_versions(route_id):
    """Получить историю версий маршрута"""
    try:
        route = TechnologicalRoute.query.get_or_404(route_id)
        
        versions = RouteVersion.query.filter_by(route_id=route_id)\
                                    .order_by(RouteVersion.version_number.desc()).all()
        
        return jsonify({
            'route_info': {
                'id': route.id,
                'name': route.name,
                'current_version': route.version
            },
            'versions': [version.to_dict() for version in versions]
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении версий маршрута'}), 500

@bp.route('/api/routes/<int:route_id>/versions', methods=['POST'])
@jwt_required()
@require_permission('routes:update')
def create_route_version(route_id):
    """Создать новую версию маршрута"""
    try:
        route = TechnologicalRoute.query.get_or_404(route_id)
        data = request.get_json()
        
        current_user_id = get_jwt_identity()
        description = data.get('description', f'Версия {route.version + 1}')
        
        new_version = route.create_version(description, current_user_id)
        db.session.commit()
        
        log_audit_event('route_version_created', f'Создана версия {new_version.version_number} маршрута {route.name}', True)
        
        return jsonify(new_version.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при создании версии маршрута'}), 500

@bp.route('/api/routes/<int:route_id>/versions/<int:version_id>', methods=['GET'])
@jwt_required()
@require_permission('routes:read')
def get_route_version(route_id, version_id):
    """Получить конкретную версию маршрута"""
    try:
        route = TechnologicalRoute.query.get_or_404(route_id)
        version = RouteVersion.query.filter_by(route_id=route_id, id=version_id).first()
        
        if not version:
            return jsonify({'error': 'Версия не найдена'}), 404
        
        return jsonify(version.to_dict())
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении версии маршрута'}), 500

@bp.route('/api/routes/<int:route_id>/versions/diff/<int:v1>/<int:v2>', methods=['GET'])
@jwt_required()
@require_permission('routes:read')
def compare_route_versions(route_id, v1, v2):
    """Сравнить две версии маршрута"""
    try:
        route = TechnologicalRoute.query.get_or_404(route_id)
        
        version1 = RouteVersion.query.filter_by(route_id=route_id, version_number=v1).first()
        version2 = RouteVersion.query.filter_by(route_id=route_id, version_number=v2).first()
        
        if not version1 or not version2:
            return jsonify({'error': 'Одна из версий не найдена'}), 404
        
        data1 = json.loads(version1.route_data)
        data2 = json.loads(version2.route_data)
        
        # Простое сравнение - можно расширить для более детального анализа
        diff = {
            'version1': {
                'number': version1.version_number,
                'data': data1,
                'created_at': version1.created_at.isoformat(),
                'created_by': version1.creator.username if version1.creator else None
            },
            'version2': {
                'number': version2.version_number,
                'data': data2,
                'created_at': version2.created_at.isoformat(),
                'created_by': version2.creator.username if version2.creator else None
            },
            'changes': []
        }
        
        # Сравнить основные поля
        for field in ['name', 'description', 'status', 'estimated_duration', 'complexity_level']:
            if data1.get(field) != data2.get(field):
                diff['changes'].append({
                    'field': field,
                    'old_value': data1.get(field),
                    'new_value': data2.get(field)
                })
        
        # Сравнить операции
        ops1 = set([op['id'] for op in data1.get('operations', [])])
        ops2 = set([op['id'] for op in data2.get('operations', [])])
        
        if ops1 != ops2:
            diff['changes'].append({
                'field': 'operations',
                'old_value': list(ops1),
                'new_value': list(ops2),
                'added_operations': list(ops2 - ops1),
                'removed_operations': list(ops1 - ops2)
            })
        
        return jsonify(diff)
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при сравнении версий маршрута'}), 500 