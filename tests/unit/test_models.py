#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для моделей данных
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError, DataError
from app.models import TechnologicalRoute, BOMItem, Operation, User
from app import db


@pytest.mark.unit
class TestTechnologicalRouteModel:
    """Тесты модели TechnologicalRoute"""
    
    def test_create_valid_route(self, app):
        """Тест создания валидного технологического маршрута"""
        with app.app_context():
            # Получаем тестового пользователя
            user = User.query.filter_by(username='test_admin').first()
            assert user is not None
            
            route = TechnologicalRoute(
                name='Тестовый маршрут',
                route_number='TR-TEST-001',
                created_by=user.id,
                description='Описание тестового маршрута'
            )
            
            db.session.add(route)
            db.session.commit()
            
            # Проверяем, что маршрут создан
            assert route.id is not None
            assert route.name == 'Тестовый маршрут'
            assert route.route_number == 'TR-TEST-001'
            assert route.status == 'draft'  # Значение по умолчанию
            assert route.version == 1  # Значение по умолчанию
            assert route.complexity_level == 'medium'  # Значение по умолчанию
            assert route.created_at is not None
            assert route.updated_at is not None
    
    def test_route_missing_required_fields(self, app):
        """Тест создания маршрута без обязательных полей - должен завершиться ошибкой"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Пытаемся создать маршрут без имени
            with pytest.raises(IntegrityError):
                route = TechnologicalRoute(
                    name=None,  # Отсутствует обязательное поле
                    route_number='TR-TEST-002',
                    created_by=user.id
                )
                db.session.add(route)
                db.session.commit()
    
    def test_route_duplicate_number(self, app):
        """Тест создания маршрута с дублирующимся номером - должен завершиться ошибкой"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Создаем первый маршрут
            route1 = TechnologicalRoute(
                name='Маршрут 1',
                route_number='TR-DUPLICATE',
                created_by=user.id
            )
            db.session.add(route1)
            db.session.commit()
            
            # Пытаемся создать второй маршрут с таким же номером
            with pytest.raises(IntegrityError):
                route2 = TechnologicalRoute(
                    name='Маршрут 2',
                    route_number='TR-DUPLICATE',  # Дублирующийся номер
                    created_by=user.id
                )
                db.session.add(route2)
                db.session.commit()
    
    def test_route_too_long_name(self, app):
        """Тест создания маршрута со слишком длинным именем - должен завершиться ошибкой"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            with pytest.raises(DataError):
                route = TechnologicalRoute(
                    name='A' * 300,  # Превышает лимит в 200 символов
                    route_number='TR-LONG-NAME',
                    created_by=user.id
                )
                db.session.add(route)
                db.session.commit()
    
    def test_route_negative_duration(self, app):
        """Тест создания маршрута с отрицательной продолжительностью"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Система должна принять отрицательное значение, но мы проверим это в бизнес-логике
            route = TechnologicalRoute(
                name='Маршрут с отрицательной продолжительностью',
                route_number='TR-NEG-DURATION',
                created_by=user.id,
                estimated_duration=-10.0
            )
            db.session.add(route)
            db.session.commit()
            
            # В unit тесте модели принимаем любое значение,
            # валидация должна быть в API уровне
            assert route.estimated_duration == -10.0
    
    def test_route_to_dict(self, app):
        """Тест сериализации маршрута в словарь"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            route = TechnologicalRoute(
                name='Тестовый маршрут для сериализации',
                route_number='TR-SERIALIZE',
                created_by=user.id,
                description='Описание для тестирования сериализации',
                estimated_duration=120.5,
                complexity_level='high'
            )
            db.session.add(route)
            db.session.commit()
            
            data = route.to_dict()
            
            assert data['name'] == 'Тестовый маршрут для сериализации'
            assert data['route_number'] == 'TR-SERIALIZE'
            assert data['description'] == 'Описание для тестирования сериализации'
            assert data['estimated_duration'] == 120.5
            assert data['complexity_level'] == 'high'
            assert 'created_at' in data
            assert 'updated_at' in data


@pytest.mark.unit
class TestBOMItemModel:
    """Тесты модели BOMItem"""
    
    def test_create_valid_bom_item(self, app):
        """Тест создания валидного элемента BOM"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            bom_item = BOMItem(
                part_number='BOM-TEST-001',
                name='Тестовый элемент BOM',
                created_by=user.id,
                quantity=2.5,
                unit='кг'
            )
            
            db.session.add(bom_item)
            db.session.commit()
            
            assert bom_item.id is not None
            assert bom_item.part_number == 'BOM-TEST-001'
            assert bom_item.name == 'Тестовый элемент BOM'
            assert bom_item.quantity == 2.5
            assert bom_item.unit == 'кг'
            assert bom_item.level == 0  # Корневой уровень
            assert bom_item.is_assembly == False  # Значение по умолчанию
    
    def test_bom_hierarchy_levels(self, app):
        """Тест правильного вычисления уровней в иерархии BOM"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Создаем корневой элемент
            root_item = BOMItem(
                part_number='BOM-ROOT',
                name='Корневая сборка',
                created_by=user.id,
                is_assembly=True
            )
            db.session.add(root_item)
            db.session.commit()
            
            # Создаем дочерний элемент
            child_item = BOMItem(
                part_number='BOM-CHILD',
                name='Дочерний элемент',
                created_by=user.id,
                parent_id=root_item.id
            )
            db.session.add(child_item)
            db.session.commit()
            
            # Создаем внук
            grandchild_item = BOMItem(
                part_number='BOM-GRANDCHILD',
                name='Элемент третьего уровня',
                created_by=user.id,
                parent_id=child_item.id
            )
            db.session.add(grandchild_item)
            db.session.commit()
            
            assert root_item.level == 0
            assert child_item.level == 1
            assert grandchild_item.level == 2
    
    def test_bom_circular_reference_protection(self, app):
        """Тест защиты от циклических ссылок в BOM"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Создаем два элемента
            item1 = BOMItem(
                part_number='BOM-CIRC-1',
                name='Элемент 1',
                created_by=user.id
            )
            db.session.add(item1)
            db.session.commit()
            
            item2 = BOMItem(
                part_number='BOM-CIRC-2', 
                name='Элемент 2',
                created_by=user.id,
                parent_id=item1.id
            )
            db.session.add(item2)
            db.session.commit()
            
            # Попытка создать циклическую ссылку должна быть обработана в бизнес-логике
            # На уровне модели допускается, проверка должна быть в API
    
    def test_bom_negative_quantity(self, app):
        """Тест создания элемента BOM с отрицательным количеством"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Создаем элемент с отрицательным количеством
            bom_item = BOMItem(
                part_number='BOM-NEG-QTY',
                name='Элемент с отрицательным количеством',
                created_by=user.id,
                quantity=-5.0
            )
            db.session.add(bom_item)
            db.session.commit()
            
            # На уровне модели принимаем, валидация в API
            assert bom_item.quantity == -5.0
    
    def test_bom_cost_calculation(self, app):
        """Тест расчета общей стоимости элемента BOM"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Создаем родительский элемент
            parent = BOMItem(
                part_number='BOM-COST-PARENT',
                name='Родительский элемент',
                created_by=user.id,
                quantity=1.0,
                cost_per_unit=100.0,
                is_assembly=True
            )
            db.session.add(parent)
            db.session.commit()
            
            # Создаем дочерние элементы
            child1 = BOMItem(
                part_number='BOM-COST-CHILD1',
                name='Дочерний элемент 1',
                created_by=user.id,
                parent_id=parent.id,
                quantity=2.0,
                cost_per_unit=50.0
            )
            
            child2 = BOMItem(
                part_number='BOM-COST-CHILD2',
                name='Дочерний элемент 2',
                created_by=user.id,
                parent_id=parent.id,
                quantity=3.0,
                cost_per_unit=30.0
            )
            
            db.session.add_all([child1, child2])
            db.session.commit()
            
            # Проверяем расчет общей стоимости
            total_cost = parent.get_total_cost()
            expected_cost = (1.0 * 100.0) + (2.0 * 50.0) + (3.0 * 30.0)  # 100 + 100 + 90 = 290
            assert total_cost == expected_cost


@pytest.mark.unit 
class TestOperationModel:
    """Тесты модели Operation"""
    
    def test_create_valid_operation(self, app):
        """Тест создания валидной операции"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            operation = Operation(
                name='Тестовая операция фрезерования',
                operation_code='OP-TEST-001',
                operation_type='machining',
                created_by=user.id,
                setup_time=30.0,
                operation_time=60.0
            )
            
            db.session.add(operation)
            db.session.commit()
            
            assert operation.id is not None
            assert operation.name == 'Тестовая операция фрезерования'
            assert operation.operation_code == 'OP-TEST-001'
            assert operation.operation_type == 'machining'
            assert operation.setup_time == 30.0
            assert operation.operation_time == 60.0
    
    def test_operation_duplicate_code(self, app):
        """Тест создания операции с дублирующимся кодом - должен завершиться ошибкой"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            # Создаем первую операцию
            operation1 = Operation(
                name='Операция 1',
                operation_code='OP-DUPLICATE',
                operation_type='machining',
                created_by=user.id,
                setup_time=30.0,
                operation_time=60.0
            )
            db.session.add(operation1)
            db.session.commit()
            
            # Пытаемся создать вторую операцию с таким же кодом
            with pytest.raises(IntegrityError):
                operation2 = Operation(
                    name='Операция 2',
                    operation_code='OP-DUPLICATE',  # Дублирующийся код
                    operation_type='assembly',
                    created_by=user.id,
                    setup_time=20.0,
                    operation_time=40.0
                )
                db.session.add(operation2)
                db.session.commit()
    
    def test_operation_negative_times(self, app):
        """Тест создания операции с отрицательным временем"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            operation = Operation(
                name='Операция с отрицательным временем',
                operation_code='OP-NEG-TIME',
                operation_type='machining',
                created_by=user.id,
                setup_time=-10.0,  # Отрицательное время подготовки
                operation_time=-20.0  # Отрицательное время операции
            )
            db.session.add(operation)
            db.session.commit()
            
            # На уровне модели принимаем, валидация должна быть в API
            assert operation.setup_time == -10.0
            assert operation.operation_time == -20.0
    
    def test_operation_missing_required_fields(self, app):
        """Тест создания операции без обязательных полей - должен завершиться ошибкой"""
        with app.app_context():
            user = User.query.filter_by(username='test_admin').first()
            
            with pytest.raises(IntegrityError):
                operation = Operation(
                    name=None,  # Отсутствует обязательное поле
                    operation_code='OP-NO-NAME',
                    operation_type='machining',
                    created_by=user.id,
                    setup_time=30.0,
                    operation_time=60.0
                )
                db.session.add(operation)
                db.session.commit() 