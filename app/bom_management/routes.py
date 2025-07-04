from flask import request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import io
import csv
import pandas as pd
from app import db
from app.models import BOMItem, User, BOMVersion, Archive
from app.bom_management import bp
from app.utils import require_permission, log_audit_event, validate_bom_data
from sqlalchemy.exc import IntegrityError
from datetime import datetime

@bp.route('/api/bom', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def get_bom_tree():
    """Получить иерархическую структуру BOM"""
    try:
        # Получить только корневые элементы (без родителя)
        root_items = BOMItem.query.filter(BOMItem.parent_id == None).all()
        
        bom_tree = []
        for item in root_items:
            bom_tree.append(item.get_tree_structure())
        
        return jsonify({
            'bom_tree': bom_tree,
            'total_items': BOMItem.query.count()
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении структуры BOM'}), 500

@bp.route('/api/bom/<int:bom_id>', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def get_bom_item(bom_id):
    """Получить BOM элемент по ID"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        
        log_audit_event('bom_item_viewed', f'Просмотр элемента BOM: {item.name}', True)
        
        return jsonify(item.to_dict())
        
    except Exception as e:
        log_audit_event('bom_item_view_error', f'Ошибка при получении элемента BOM {bom_id}: {str(e)}', False)
        return jsonify({'error': 'Ошибка при получении элемента BOM'}), 500

@bp.route('/api/bom/<int:bom_id>', methods=['PUT'])
@jwt_required()
@require_permission('bom:update')
def update_bom_item(bom_id):
    """Обновить BOM элемент"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        data = request.get_json()
        
        # Проверка версии для контроля конкурентности
        if 'version' in data and data['version'] != item.version:
            return jsonify({
                'error': 'Конфликт версий. Данные были изменены другим пользователем. Обновите страницу.',
                'current_version': item.version,
                'provided_version': data['version']
            }), 409
        
        # Создать версию перед изменением
        item.create_version('Изменение перед обновлением', get_jwt_identity())
        
        # Обновить поля
        if 'name' in data:
            item.name = data['name']
        if 'description' in data:
            item.description = data['description']
        if 'part_number' in data:
            item.part_number = data['part_number']
        if 'quantity' in data:
            item.quantity = data['quantity']
        if 'unit' in data:
            item.unit = data['unit']
        if 'material_type' in data:
            item.material_type = data['material_type']
        if 'cost_per_unit' in data:
            item.cost_per_unit = data['cost_per_unit']
        if 'currency' in data:
            item.currency = data['currency']
        if 'is_assembly' in data:
            item.is_assembly = data['is_assembly']
        if 'status' in data:
            item.status = data['status']
        if 'technological_route_id' in data:
            item.technological_route_id = data['technological_route_id']
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit_event('bom_item_updated', f'Обновлен элемент BOM: {item.name}', True)
        
        return jsonify(item.to_dict())
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Элемент BOM с таким номером детали уже существует'}), 409
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_item_update_error', f'Ошибка при обновлении элемента BOM {bom_id}: {str(e)}', False)
        return jsonify({'error': 'Ошибка при обновлении элемента BOM'}), 500

@bp.route('/api/bom/<int:bom_id>', methods=['DELETE'])
@jwt_required()
@require_permission('bom:delete')
def delete_bom_item(bom_id):
    """Удалить BOM элемент с архивированием"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        current_user_id = get_jwt_identity()
        
        # Архивирование перед удалением
        archive_data = item.to_dict()
        archive_data['children'] = [child.to_dict() for child in item.children]
        archive_data['versions'] = [v.to_dict() for v in item.versions]
        
        archive = Archive(
            entity_type='bom_item',
            entity_id=item.id,
            entity_data=json.dumps(archive_data, ensure_ascii=False),
            archived_by=current_user_id,
            reason='deleted',
            notes=f'BOM элемент удален: {item.name}'
        )
        
        db.session.add(archive)
        
        # Архивировать дочерние элементы каскадно
        def archive_children(parent_item):
            for child in parent_item.children:
                archive_children(child)  # Рекурсивно архивировать внуков
                child_archive_data = child.to_dict()
                child_archive = Archive(
                    entity_type='bom_item',
                    entity_id=child.id,
                    entity_data=json.dumps(child_archive_data, ensure_ascii=False),
                    archived_by=current_user_id,
                    reason='parent_deleted',
                    notes=f'BOM элемент удален каскадно: {child.name}'
                )
                db.session.add(child_archive)
        
        archive_children(item)
        
        # Удаление элемента (дочерние удалятся каскадно)
        item_name = item.name
        db.session.delete(item)
        db.session.commit()
        
        log_audit_event('bom_item_deleted', f'Удален элемент BOM: {item_name}', True)
        
        return jsonify({'message': 'Элемент BOM успешно удален и заархивирован'})
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_item_deletion_error', f'Ошибка при удалении элемента BOM {bom_id}: {str(e)}', False)
        return jsonify({'error': 'Ошибка при удалении элемента BOM'}), 500

@bp.route('/api/bom/<int:bom_id>/tree', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def get_bom_tree_from_item(bom_id):
    """Получить полное дерево BOM от указанного элемента"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        
        tree_structure = item.get_tree_structure()
        
        return jsonify({
            'tree': tree_structure,
            'total_cost': item.get_total_cost(),
            'item_count': len(item.children) + 1  # включая сам элемент
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении дерева BOM'}), 500

@bp.route('/api/bom/items', methods=['POST'])
@jwt_required()
@require_permission('bom:create')
def create_bom_item():
    """Создать новый элемент BOM"""
    try:
        data = request.get_json()
        
        # Комплексная валидация и санитизация
        try:
            data = validate_bom_data(data)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        current_user_id = get_jwt_identity()
        
        # Создание элемента BOM
        item = BOMItem(
            part_number=data['part_number'],
            name=data['name'],
            created_by=current_user_id,
            parent_id=data.get('parent_id'),
            quantity=data.get('quantity', 1.0),
            unit=data.get('unit', 'шт')
        )
        
        # Дополнительные параметры
        if 'description' in data:
            item.description = data['description']
        if 'material_type' in data:
            item.material_type = data['material_type']
        if 'cost_per_unit' in data:
            item.cost_per_unit = data['cost_per_unit']
        if 'currency' in data:
            item.currency = data['currency']
        if 'is_assembly' in data:
            item.is_assembly = data['is_assembly']
        if 'status' in data:
            item.status = data['status']
        if 'technological_route_id' in data:
            item.technological_route_id = data['technological_route_id']
        
        db.session.add(item)
        db.session.commit()
        
        log_audit_event('bom_item_created', f'Создан элемент BOM: {item.name} ({item.part_number})', True)
        
        return jsonify(item.to_dict()), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Элемент BOM с таким номером детали уже существует'}), 409
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"BOM creation error: {str(e)}")
        print(f"Traceback: {error_details}")
        log_audit_event('bom_item_creation_error', f'Ошибка при создании элемента BOM: {str(e)}', False)
        return jsonify({'error': f'Ошибка при создании элемента BOM: {str(e)}'}), 500

@bp.route('/api/bom/<int:bom_id>/items', methods=['POST'])
@jwt_required()
@require_permission('bom:create')
def add_bom_child_item(bom_id):
    """Добавить дочерний элемент в BOM"""
    try:
        parent = BOMItem.query.get_or_404(bom_id)
        data = request.get_json()
        
        # Валидация
        if not data.get('part_number'):
            return jsonify({'error': 'Номер детали обязателен'}), 400
        
        if not data.get('name'):
            return jsonify({'error': 'Название обязательно'}), 400
        
        current_user_id = get_jwt_identity()
        
        # Создание дочернего элемента
        child_item = BOMItem(
            part_number=data['part_number'],
            name=data['name'],
            created_by=current_user_id,
            parent_id=bom_id,
            quantity=data.get('quantity', 1.0),
            unit=data.get('unit', 'шт')
        )
        
        # Дополнительные параметры
        if 'description' in data:
            child_item.description = data['description']
        if 'material_type' in data:
            child_item.material_type = data['material_type']
        if 'cost_per_unit' in data:
            child_item.cost_per_unit = data['cost_per_unit']
        if 'currency' in data:
            child_item.currency = data['currency']
        if 'is_assembly' in data:
            child_item.is_assembly = data['is_assembly']
        if 'status' in data:
            child_item.status = data['status']
        if 'technological_route_id' in data:
            child_item.technological_route_id = data['technological_route_id']
        
        db.session.add(child_item)
        db.session.commit()
        
        log_audit_event('bom_child_item_created', f'Добавлен дочерний элемент {child_item.name} к {parent.name}', True)
        
        return jsonify(child_item.to_dict()), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Элемент BOM с таким номером детали уже существует'}), 409
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_child_item_creation_error', f'Ошибка при добавлении дочернего элемента: {str(e)}', False)
        return jsonify({'error': 'Ошибка при добавлении дочернего элемента'}), 500

@bp.route('/api/bom/<int:bom_id>/items/<int:item_id>', methods=['PUT'])
@jwt_required()
@require_permission('bom:update')
def update_bom_child_item(bom_id, item_id):
    """Обновить дочерний элемент BOM"""
    try:
        parent = BOMItem.query.get_or_404(bom_id)
        item = BOMItem.query.get_or_404(item_id)
        
        # Проверить, что элемент действительно дочерний
        if item.parent_id != bom_id:
            return jsonify({'error': 'Элемент не является дочерним для указанного родителя'}), 400
        
        data = request.get_json()
        
        # Проверка версии для контроля конкурентности
        if 'version' in data and data['version'] != item.version:
            return jsonify({
                'error': 'Конфликт версий. Данные были изменены другим пользователем. Обновите страницу.',
                'current_version': item.version,
                'provided_version': data['version']
            }), 409
        
        # Создать версию перед изменением
        item.create_version('Изменение дочернего элемента', get_jwt_identity())
        
        # Обновить поля
        if 'name' in data:
            item.name = data['name']
        if 'description' in data:
            item.description = data['description']
        if 'part_number' in data:
            item.part_number = data['part_number']
        if 'quantity' in data:
            item.quantity = data['quantity']
        if 'unit' in data:
            item.unit = data['unit']
        if 'material_type' in data:
            item.material_type = data['material_type']
        if 'cost_per_unit' in data:
            item.cost_per_unit = data['cost_per_unit']
        if 'currency' in data:
            item.currency = data['currency']
        if 'is_assembly' in data:
            item.is_assembly = data['is_assembly']
        if 'status' in data:
            item.status = data['status']
        if 'technological_route_id' in data:
            item.technological_route_id = data['technological_route_id']
        
        item.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit_event('bom_child_item_updated', f'Обновлен дочерний элемент {item.name} у {parent.name}', True)
        
        return jsonify(item.to_dict())
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Элемент BOM с таким номером детали уже существует'}), 409
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_child_item_update_error', f'Ошибка при обновлении дочернего элемента: {str(e)}', False)
        return jsonify({'error': 'Ошибка при обновлении дочернего элемента'}), 500

@bp.route('/api/bom/<int:bom_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@require_permission('bom:delete')
def delete_bom_child_item(bom_id, item_id):
    """Удалить дочерний элемент BOM"""
    try:
        parent = BOMItem.query.get_or_404(bom_id)
        item = BOMItem.query.get_or_404(item_id)
        
        # Проверить, что элемент действительно дочерний
        if item.parent_id != bom_id:
            return jsonify({'error': 'Элемент не является дочерним для указанного родителя'}), 400
        
        current_user_id = get_jwt_identity()
        
        # Архивирование перед удалением
        archive_data = item.to_dict()
        archive_data['children'] = [child.to_dict() for child in item.children]
        
        archive = Archive(
            entity_type='bom_item',
            entity_id=item.id,
            entity_data=json.dumps(archive_data, ensure_ascii=False),
            archived_by=current_user_id,
            reason='deleted',
            notes=f'Дочерний элемент BOM удален: {item.name}'
        )
        
        db.session.add(archive)
        
        item_name = item.name
        db.session.delete(item)
        db.session.commit()
        
        log_audit_event('bom_child_item_deleted', f'Удален дочерний элемент {item_name} у {parent.name}', True)
        
        return jsonify({'message': 'Дочерний элемент BOM успешно удален'})
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_child_item_deletion_error', f'Ошибка при удалении дочернего элемента: {str(e)}', False)
        return jsonify({'error': 'Ошибка при удалении дочернего элемента'}), 500

@bp.route('/api/bom/export/csv', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def export_bom_csv():
    """Экспорт BOM в CSV формат"""
    try:
        # Получить все элементы BOM
        items = BOMItem.query.all()
        
        # Создать CSV в памяти
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        headers = [
            'ID', 'Part Number', 'Name', 'Description', 'Parent ID', 
            'Quantity', 'Unit', 'Material Type', 'Cost Per Unit', 'Currency',
            'Level', 'Is Assembly', 'Status', 'Created By', 'Created At'
        ]
        writer.writerow(headers)
        
        # Данные
        for item in items:
            writer.writerow([
                item.id,
                item.part_number,
                item.name,
                item.description or '',
                item.parent_id or '',
                item.quantity,
                item.unit,
                item.material_type or '',
                float(item.cost_per_unit) if item.cost_per_unit else '',
                item.currency,
                item.level,
                item.is_assembly,
                item.status,
                item.creator.username if item.creator else '',
                item.created_at.isoformat()
            ])
        
        # Подготовить файл для скачивания
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        log_audit_event('bom_exported', 'Экспорт BOM в CSV формат', True)
        
        return jsonify({
            'csv_data': csv_data,
            'filename': f'bom_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        log_audit_event('bom_export_error', f'Ошибка при экспорте BOM: {str(e)}', False)
        return jsonify({'error': 'Ошибка при экспорте BOM'}), 500

@bp.route('/api/bom/<int:bom_id>/versions', methods=['POST'])
@jwt_required()
@require_permission('bom:update')
def create_bom_version(bom_id):
    """Создать новую версию BOM элемента"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        data = request.get_json()
        
        description = data.get('description', f'Версия {item.version + 1}')
        current_user_id = get_jwt_identity()
        
        new_version = item.create_version(description, current_user_id)
        db.session.commit()
        
        log_audit_event('bom_version_created', f'Создана версия {new_version.version_number} для BOM {item.name}', True)
        
        return jsonify(new_version.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_version_creation_error', f'Ошибка при создании версии BOM: {str(e)}', False)
        return jsonify({'error': 'Ошибка при создании версии BOM'}), 500

@bp.route('/api/bom/<int:bom_id>/versions', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def get_bom_versions(bom_id):
    """Получить историю версий BOM элемента"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        
        versions = BOMVersion.query.filter_by(bom_item_id=bom_id)\
                                  .order_by(BOMVersion.version_number.desc()).all()
        
        return jsonify({
            'bom_info': {
                'id': item.id,
                'name': item.name,
                'part_number': item.part_number,
                'current_version': item.version
            },
            'versions': [version.to_dict() for version in versions]
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении версий BOM'}), 500

@bp.route('/api/bom/<int:bom_id>/versions/<int:version_id>', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def get_bom_version(bom_id, version_id):
    """Получить конкретную версию BOM элемента"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        version = BOMVersion.query.filter_by(bom_item_id=bom_id, id=version_id).first()
        if not version:
            return jsonify({'error': 'Версия не найдена'}), 404
        
        return jsonify(version.to_dict())
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении версии BOM'}), 500

@bp.route('/api/bom/<int:bom_id>/versions/diff/<int:v1>/<int:v2>', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def compare_bom_versions(bom_id, v1, v2):
    """Сравнить две версии BOM элемента"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        
        version1 = BOMVersion.query.filter_by(bom_item_id=bom_id, version_number=v1).first()
        version2 = BOMVersion.query.filter_by(bom_item_id=bom_id, version_number=v2).first()
        
        if not version1 or not version2:
            return jsonify({'error': 'Одна из версий не найдена'}), 404
        
        data1 = json.loads(version1.bom_data)
        data2 = json.loads(version2.bom_data)
        
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
        for field in ['name', 'description', 'part_number', 'quantity', 'unit', 'cost_per_unit']:
            if data1.get(field) != data2.get(field):
                diff['changes'].append({
                    'field': field,
                    'old_value': data1.get(field),
                    'new_value': data2.get(field)
                })
        
        return jsonify(diff)
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при сравнении версий BOM'}), 500

@bp.route('/api/bom/import/excel', methods=['POST'])
@jwt_required()
@require_permission('bom:create')
def import_bom_excel():
    """Импорт BOM из Excel файла"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не предоставлен'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Поддерживаются только Excel файлы (.xlsx, .xls)'}), 400
        
        current_user_id = get_jwt_identity()
        
        # Читаем Excel файл
        df = pd.read_excel(file)
        
        # Проверяем обязательные столбцы
        required_columns = ['part_number', 'name', 'quantity']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Отсутствуют обязательные столбцы: {", ".join(missing_columns)}'}), 400
        
        imported_items = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Создание элемента BOM
                item_data = {
                    'part_number': str(row['part_number']),
                    'name': str(row['name']),
                    'quantity': float(row.get('quantity', 1.0)),
                    'unit': str(row.get('unit', 'шт')),
                    'description': str(row.get('description', '')) if pd.notna(row.get('description')) else None,
                    'material_type': str(row.get('material_type', '')) if pd.notna(row.get('material_type')) else None,
                    'cost_per_unit': float(row.get('cost_per_unit', 0)) if pd.notna(row.get('cost_per_unit')) else None,
                    'currency': str(row.get('currency', 'RUB')),
                    'is_assembly': bool(row.get('is_assembly', False)),
                    'status': str(row.get('status', 'draft')),
                    'parent_id': int(row.get('parent_id')) if pd.notna(row.get('parent_id')) else None
                }
                
                # Проверить, что родитель существует если указан
                if item_data['parent_id']:
                    parent = BOMItem.query.get(item_data['parent_id'])
                    if not parent:
                        errors.append(f'Строка {index + 1}: Родительский элемент с ID {item_data["parent_id"]} не найден')
                        continue
                
                item = BOMItem(
                    part_number=item_data['part_number'],
                    name=item_data['name'],
                    created_by=current_user_id,
                    parent_id=item_data['parent_id'],
                    quantity=item_data['quantity'],
                    unit=item_data['unit']
                )
                
                # Установить дополнительные поля
                for field in ['description', 'material_type', 'cost_per_unit', 'currency', 'is_assembly', 'status']:
                    if item_data[field] is not None:
                        setattr(item, field, item_data[field])
                
                db.session.add(item)
                db.session.flush()  # Получить ID без коммита
                
                imported_items.append({
                    'row': index + 1,
                    'part_number': item.part_number,
                    'name': item.name,
                    'id': item.id
                })
                
            except Exception as e:
                errors.append(f'Строка {index + 1}: {str(e)}')
        
        if errors:
            db.session.rollback()
            return jsonify({
                'error': 'Ошибки при импорте',
                'errors': errors,
                'imported_count': 0
            }), 400
        
        db.session.commit()
        
        log_audit_event('bom_excel_imported', f'Импортировано {len(imported_items)} элементов BOM из Excel', True)
        
        return jsonify({
            'message': f'Успешно импортировано {len(imported_items)} элементов',
            'imported_items': imported_items,
            'imported_count': len(imported_items)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_excel_import_error', f'Ошибка при импорте Excel: {str(e)}', False)
        return jsonify({'error': f'Ошибка при импорте Excel: {str(e)}'}), 500

@bp.route('/api/bom/import/csv', methods=['POST'])
@jwt_required()
@require_permission('bom:create')
def import_bom_csv():
    """Импорт BOM из CSV файла"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не предоставлен'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not file.filename or not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Поддерживаются только CSV файлы'}), 400
        
        current_user_id = get_jwt_identity()
        
        # Читаем CSV файл
        try:
            # Попробуем UTF-8 сначала
            file_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Если не получилось, попробуем CP1251
            file.seek(0)
            file_content = file.read().decode('cp1251')
        
        df = pd.read_csv(io.StringIO(file_content))
        
        # Проверяем обязательные столбцы
        required_columns = ['part_number', 'name', 'quantity']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Отсутствуют обязательные столбцы: {", ".join(missing_columns)}'}), 400
        
        imported_items = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Создание элемента BOM
                item_data = {
                    'part_number': str(row['part_number']),
                    'name': str(row['name']),
                    'quantity': float(row.get('quantity', 1.0)),
                    'unit': str(row.get('unit', 'шт')),
                    'description': str(row.get('description', '')) if pd.notna(row.get('description')) else None,
                    'material_type': str(row.get('material_type', '')) if pd.notna(row.get('material_type')) else None,
                    'cost_per_unit': float(row.get('cost_per_unit', 0)) if pd.notna(row.get('cost_per_unit')) else None,
                    'currency': str(row.get('currency', 'RUB')),
                    'is_assembly': bool(row.get('is_assembly', False)),
                    'status': str(row.get('status', 'draft')),
                    'parent_id': int(row.get('parent_id')) if pd.notna(row.get('parent_id')) else None
                }
                
                # Проверить, что родитель существует если указан
                if item_data['parent_id']:
                    parent = BOMItem.query.get(item_data['parent_id'])
                    if not parent:
                        errors.append(f'Строка {index + 1}: Родительский элемент с ID {item_data["parent_id"]} не найден')
                        continue
                
                item = BOMItem(
                    part_number=item_data['part_number'],
                    name=item_data['name'],
                    created_by=current_user_id,
                    parent_id=item_data['parent_id'],
                    quantity=item_data['quantity'],
                    unit=item_data['unit']
                )
                
                # Установить дополнительные поля
                for field in ['description', 'material_type', 'cost_per_unit', 'currency', 'is_assembly', 'status']:
                    if item_data[field] is not None:
                        setattr(item, field, item_data[field])
                
                db.session.add(item)
                db.session.flush()  # Получить ID без коммита
                
                imported_items.append({
                    'row': index + 1,
                    'part_number': item.part_number,
                    'name': item.name,
                    'id': item.id
                })
                
            except Exception as e:
                errors.append(f'Строка {index + 1}: {str(e)}')
        
        if errors:
            db.session.rollback()
            return jsonify({
                'error': 'Ошибки при импорте',
                'errors': errors,
                'imported_count': 0
            }), 400
        
        db.session.commit()
        
        log_audit_event('bom_csv_imported', f'Импортировано {len(imported_items)} элементов BOM из CSV', True)
        
        return jsonify({
            'message': f'Успешно импортировано {len(imported_items)} элементов',
            'imported_items': imported_items,
            'imported_count': len(imported_items)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('bom_csv_import_error', f'Ошибка при импорте CSV: {str(e)}', False)
        return jsonify({'error': f'Ошибка при импорте CSV: {str(e)}'}), 500

@bp.route('/api/bom/<int:bom_id>/export/excel', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def export_bom_excel(bom_id):
    """Экспорт конкретного BOM элемента и его дерева в Excel"""
    try:
        item = BOMItem.query.get_or_404(bom_id)
        
        # Получить полное дерево
        def get_all_descendants(bom_item, level=0):
            items = [bom_item]
            for child in bom_item.children:
                items.extend(get_all_descendants(child, level + 1))
            return items
        
        all_items = get_all_descendants(item)
        
        # Подготовить данные для Excel
        data = []
        for bom_item in all_items:
            data.append({
                'ID': bom_item.id,
                'Part Number': bom_item.part_number,
                'Name': bom_item.name,
                'Description': bom_item.description or '',
                'Parent ID': bom_item.parent_id or '',
                'Quantity': bom_item.quantity,
                'Unit': bom_item.unit,
                'Material Type': bom_item.material_type or '',
                'Cost Per Unit': float(bom_item.cost_per_unit) if bom_item.cost_per_unit else '',
                'Currency': bom_item.currency,
                'Level': bom_item.level,
                'Is Assembly': bom_item.is_assembly,
                'Status': bom_item.status,
                'Created By': bom_item.creator.username if bom_item.creator else '',
                'Created At': bom_item.created_at.isoformat()
            })
        
        df = pd.DataFrame(data)
        
        # Создать Excel файл в памяти
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='BOM')
        
        output.seek(0)
        
        log_audit_event('bom_excel_exported', f'Экспорт BOM {item.name} в Excel', True)
        
        filename = f'bom_{item.part_number}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        log_audit_event('bom_excel_export_error', f'Ошибка при экспорте Excel: {str(e)}', False)
        return jsonify({'error': 'Ошибка при экспорте в Excel'}), 500

@bp.route('/api/archives', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def get_archives():
    """Получить архивные записи"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        entity_type = request.args.get('entity_type')
        
        query = Archive.query
        
        # Фильтр по типу сущности
        if entity_type:
            query = query.filter(Archive.entity_type == entity_type)
        
        # Пагинация
        archives = query.order_by(Archive.archived_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'archives': [archive.to_dict() for archive in archives.items],
            'total': archives.total,
            'pages': archives.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении архивных записей'}), 500

@bp.route('/api/archives/<int:archive_id>/restore', methods=['POST'])
@jwt_required()
@require_permission('bom:create')
def restore_from_archive(archive_id):
    """Восстановить элемент из архива"""
    try:
        archive = Archive.query.get_or_404(archive_id)
        current_user_id = get_jwt_identity()
        
        # Проверить тип сущности
        if archive.entity_type not in ['bom_item', 'route']:
            return jsonify({'error': 'Неподдерживаемый тип сущности для восстановления'}), 400
        
        # Восстановить BOM элемент
        if archive.entity_type == 'bom_item':
            archived_data = json.loads(archive.entity_data)
            
            # Создать новый элемент из архивных данных
            restored_item = BOMItem(
                part_number=archived_data['part_number'] + '_restored',  # Добавить суффикс чтобы избежать конфликтов
                name=archived_data['name'] + ' (Восстановлен)',
                created_by=current_user_id,
                quantity=archived_data.get('quantity', 1.0),
                unit=archived_data.get('unit', 'шт')
            )
            
            # Восстановить дополнительные поля
            if archived_data.get('description'):
                restored_item.description = archived_data['description']
            if archived_data.get('material_type'):
                restored_item.material_type = archived_data['material_type']
            if archived_data.get('cost_per_unit'):
                restored_item.cost_per_unit = archived_data['cost_per_unit']
            if archived_data.get('currency'):
                restored_item.currency = archived_data['currency']
            if archived_data.get('is_assembly'):
                restored_item.is_assembly = archived_data['is_assembly']
            if archived_data.get('status'):
                restored_item.status = archived_data['status']
            
            db.session.add(restored_item)
            db.session.commit()
            
            log_audit_event('archive_restored', f'Восстановлен BOM элемент из архива: {restored_item.name}', True)
            
            return jsonify({
                'message': 'Элемент успешно восстановлен из архива',
                'restored_item': restored_item.to_dict()
            }), 201
            
        return jsonify({'error': 'Восстановление этого типа сущности пока не поддерживается'}), 400
        
    except Exception as e:
        db.session.rollback()
        log_audit_event('archive_restore_error', f'Ошибка при восстановлении из архива: {str(e)}', False)
        return jsonify({'error': 'Ошибка при восстановлении из архива'}), 500 