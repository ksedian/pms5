from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from app import db
from app.models import Operation, User
from app.api import bp
from app.utils import require_permission, log_audit_event
from sqlalchemy.exc import IntegrityError

@bp.route('/operations', methods=['GET'])
@jwt_required()
@require_permission('operations:read')
def get_operations():
    """Получить список операций"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        operation_type = request.args.get('type')
        search = request.args.get('search')
        
        query = Operation.query
        
        # Фильтры
        if operation_type:
            query = query.filter(Operation.operation_type == operation_type)
        
        if search:
            query = query.filter(
                Operation.name.ilike(f'%{search}%') |
                Operation.operation_code.ilike(f'%{search}%')
            )
        
        # Пагинация
        operations = query.order_by(Operation.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'operations': [op.to_dict() for op in operations.items],
            'total': operations.total,
            'pages': operations.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении списка операций'}), 500

@bp.route('/operations', methods=['POST'])
@jwt_required()
@require_permission('operations:create')
def create_operation():
    """Создать новую операцию"""
    try:
        data = request.get_json()
        
        # Валидация
        if not data.get('name'):
            return jsonify({'error': 'Название операции обязательно'}), 400
        
        if not data.get('operation_code'):
            return jsonify({'error': 'Код операции обязателен'}), 400
        
        if not data.get('operation_type'):
            return jsonify({'error': 'Тип операции обязателен'}), 400
        
        current_user_id = get_jwt_identity()
        
        # Создание операции
        operation = Operation(
            name=data['name'],
            operation_code=data['operation_code'],
            operation_type=data['operation_type'],
            created_by=current_user_id,
            description=data.get('description')
        )
        
        # Дополнительные параметры
        if 'setup_time' in data:
            operation.setup_time = data['setup_time']
        if 'operation_time' in data:
            operation.operation_time = data['operation_time']
        if 'required_equipment' in data:
            operation.required_equipment = json.dumps(data['required_equipment'])
        if 'required_skills' in data:
            operation.required_skills = json.dumps(data['required_skills'])
        if 'quality_requirements' in data:
            operation.quality_requirements = json.dumps(data['quality_requirements'])
        
        db.session.add(operation)
        db.session.commit()
        
        log_audit_event('operation_created', f'Создана операция: {operation.name}', True)
        
        return jsonify(operation.to_dict()), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Операция с таким кодом уже существует'}), 409
    except Exception as e:
        db.session.rollback()
        log_audit_event('operation_creation_error', f'Ошибка при создании операции: {str(e)}', False)
        return jsonify({'error': 'Ошибка при создании операции'}), 500

@bp.route('/operations/<int:operation_id>', methods=['GET'])
@jwt_required()
@require_permission('operations:read')
def get_operation(operation_id):
    """Получить операцию по ID"""
    try:
        operation = Operation.query.get_or_404(operation_id)
        return jsonify(operation.to_dict())
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении операции'}), 500

@bp.route('/operations/<int:operation_id>', methods=['PUT'])
@jwt_required()
@require_permission('operations:update')
def update_operation(operation_id):
    """Обновить операцию"""
    try:
        operation = Operation.query.get_or_404(operation_id)
        data = request.get_json()
        
        # Обновление полей
        if 'name' in data:
            operation.name = data['name']
        if 'description' in data:
            operation.description = data['description']
        if 'operation_type' in data:
            operation.operation_type = data['operation_type']
        if 'setup_time' in data:
            operation.setup_time = data['setup_time']
        if 'operation_time' in data:
            operation.operation_time = data['operation_time']
        if 'required_equipment' in data:
            operation.required_equipment = json.dumps(data['required_equipment'])
        if 'required_skills' in data:
            operation.required_skills = json.dumps(data['required_skills'])
        if 'quality_requirements' in data:
            operation.quality_requirements = json.dumps(data['quality_requirements'])
        
        db.session.commit()
        
        log_audit_event('operation_updated', f'Обновлена операция: {operation.name}', True)
        
        return jsonify(operation.to_dict())
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('operation_update_error', f'Ошибка при обновлении операции {operation_id}: {str(e)}', False)
        return jsonify({'error': 'Ошибка при обновлении операции'}), 500

@bp.route('/operations/<int:operation_id>', methods=['DELETE'])
@jwt_required()
@require_permission('operations:delete')
def delete_operation(operation_id):
    """Удалить операцию"""
    try:
        operation = Operation.query.get_or_404(operation_id)
        
        # Проверить, используется ли операция в маршрутах
        if operation.routes:
            return jsonify({
                'error': 'Невозможно удалить операцию, которая используется в технологических маршрутах',
                'routes': [route.name for route in operation.routes]
            }), 409
        
        operation_name = operation.name
        db.session.delete(operation)
        db.session.commit()
        
        log_audit_event('operation_deleted', f'Удалена операция: {operation_name}', True)
        
        return jsonify({'message': 'Операция успешно удалена'})
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('operation_deletion_error', f'Ошибка при удалении операции {operation_id}: {str(e)}', False)
        return jsonify({'error': 'Ошибка при удалении операции'}), 500 