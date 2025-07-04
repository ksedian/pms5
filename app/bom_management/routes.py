from flask import request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import io
import csv
from app import db
from app.models import BOMItem, User, BOMVersion, Archive
from app.bom_management import bp
from app.utils import require_permission, log_audit_event
from sqlalchemy.exc import IntegrityError
from datetime import datetime

@bp.route('/api/bom', methods=['GET'])
@jwt_required()
@require_permission('bom:read')
def get_bom_tree():
    """Получить иерархическую структуру BOM"""
    try:
        # Получить только корневые элементы (без родителя)
        root_items = BOMItem.query.filter(BOMItem.parent_id.is_(None)).all()
        
        bom_tree = []
        for item in root_items:
            bom_tree.append(item.get_tree_structure())
        
        return jsonify({
            'bom_tree': bom_tree,
            'total_items': BOMItem.query.count()
        })
        
    except Exception as e:
        return jsonify({'error': 'Ошибка при получении структуры BOM'}), 500

@bp.route('/api/bom/items', methods=['POST'])
@jwt_required()
@require_permission('bom:create')
def create_bom_item():
    """Создать новый элемент BOM"""
    try:
        data = request.get_json()
        
        # Валидация
        if not data.get('part_number'):
            return jsonify({'error': 'Номер детали обязателен'}), 400
        
        if not data.get('name'):
            return jsonify({'error': 'Название обязательно'}), 400
        
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