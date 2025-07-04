#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Общие fixtures и конфигурация для всех тестов
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from flask import Flask
import tempfile

# Устанавливаем переменную окружения для тестов
os.environ['FLASK_ENV'] = 'testing'

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Role, Permission, TechnologicalRoute, BOMItem, Operation
from app.config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Создание Flask приложения для тестов"""
    app = create_app('testing')
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Создаем тестовые данные
        create_test_data()
        
        yield app
        
        # Очистка после тестов
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Тестовый клиент Flask"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Сессия базы данных с rollback после каждого теста"""
    with app.app_context():
        transaction = db.session.begin()
        yield db.session
        transaction.rollback()


def create_test_data():
    """Создание базовых тестовых данных"""
    try:
        # Создаем базовые права доступа
        permissions = [
            Permission(name='routes:create', description='Создание маршрутов', resource='routes', action='create'),
            Permission(name='routes:read', description='Просмотр маршрутов', resource='routes', action='read'),
            Permission(name='routes:update', description='Изменение маршрутов', resource='routes', action='update'),
            Permission(name='routes:delete', description='Удаление маршрутов', resource='routes', action='delete'),
            Permission(name='bom:create', description='Создание BOM', resource='bom', action='create'),
            Permission(name='bom:read', description='Просмотр BOM', resource='bom', action='read'),
            Permission(name='bom:update', description='Изменение BOM', resource='bom', action='update'),
            Permission(name='bom:delete', description='Удаление BOM', resource='bom', action='delete'),
            Permission(name='operations:create', description='Создание операций', resource='operations', action='create'),
            Permission(name='operations:read', description='Просмотр операций', resource='operations', action='read'),
            Permission(name='operations:update', description='Изменение операций', resource='operations', action='update'),
            Permission(name='operations:delete', description='Удаление операций', resource='operations', action='delete'),
        ]
        
        for permission in permissions:
            db.session.add(permission)
        
        db.session.commit()
        
        # Создаем роли
        admin_role = Role(name='test_admin', description='Тестовый администратор')
        engineer_role = Role(name='test_engineer', description='Тестовый инженер')
        user_role = Role(name='test_user', description='Тестовый пользователь')
        
        # Даем админу все права
        admin_role.permissions = permissions
        # Даем инженеру права на чтение и изменение
        engineer_role.permissions = [p for p in permissions if p.action in ['read', 'create', 'update']]
        # Даем пользователю только права на чтение
        user_role.permissions = [p for p in permissions if p.action == 'read']
        
        db.session.add_all([admin_role, engineer_role, user_role])
        db.session.commit()
        
        # Создаем тестовых пользователей
        test_admin = User(
            username='test_admin',
            email='test_admin@test.com',
            password='test123'
        )
        test_admin.roles.append(admin_role)
        
        test_engineer = User(
            username='test_engineer', 
            email='test_engineer@test.com',
            password='test123'
        )
        test_engineer.roles.append(engineer_role)
        
        test_user = User(
            username='test_user',
            email='test_user@test.com', 
            password='test123'
        )
        test_user.roles.append(user_role)
        
        db.session.add_all([test_admin, test_engineer, test_user])
        db.session.commit()
        
    except Exception as e:
        print(f"Ошибка создания тестовых данных: {e}")
        db.session.rollback()


@pytest.fixture
def auth_headers_admin(client):
    """Заголовки аутентификации для администратора"""
    response = client.post('/api/auth/login', json={
        'username': 'test_admin',
        'password': 'test123'
    })
    
    if response.status_code == 200:
        token = response.json['access_token']
        return {'Authorization': f'Bearer {token}'}
    else:
        pytest.fail(f"Не удалось войти как администратор: {response.data}")


@pytest.fixture
def auth_headers_engineer(client):
    """Заголовки аутентификации для инженера"""
    response = client.post('/api/auth/login', json={
        'username': 'test_engineer',
        'password': 'test123'
    })
    
    if response.status_code == 200:
        token = response.json['access_token']
        return {'Authorization': f'Bearer {token}'}
    else:
        pytest.fail(f"Не удалось войти как инженер: {response.data}")


@pytest.fixture
def auth_headers_user(client):
    """Заголовки аутентификации для обычного пользователя"""
    response = client.post('/api/auth/login', json={
        'username': 'test_user',
        'password': 'test123'
    })
    
    if response.status_code == 200:
        token = response.json['access_token']
        return {'Authorization': f'Bearer {token}'}
    else:
        pytest.fail(f"Не удалось войти как пользователь: {response.data}")


@pytest.fixture
def sample_route_data():
    """Пример данных технологического маршрута"""
    return {
        'name': 'Тестовый технологический маршрут',
        'route_number': f'TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
        'description': 'Описание тестового маршрута',
        'status': 'draft',
        'estimated_duration': 120.5,
        'complexity_level': 'medium'
    }


@pytest.fixture
def sample_bom_data():
    """Пример данных BOM элемента"""
    return {
        'part_number': f'BOM-TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
        'name': 'Тестовый элемент BOM',
        'description': 'Описание тестового элемента',
        'quantity': 1.0,
        'unit': 'шт',
        'is_assembly': True,
        'material_type': 'steel',
        'cost_per_unit': 100.0,
        'currency': 'RUB'
    }


@pytest.fixture
def sample_operation_data():
    """Пример данных операции"""
    return {
        'name': 'Тестовая операция',
        'operation_code': f'OP-TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
        'operation_type': 'machining',
        'description': 'Описание тестовой операции',
        'setup_time': 30.0,
        'operation_time': 60.0,
        'required_equipment': 'Станок ЧПУ',
        'required_skills': 'Оператор ЧПУ'
    }


@pytest.fixture
def invalid_data_samples():
    """Примеры некорректных данных для негативных тестов"""
    return {
        'empty_name': {'name': '', 'route_number': 'TEST-123'},
        'missing_route_number': {'name': 'Test Route'},
        'sql_injection': {
            'name': "'; DROP TABLE technological_routes; --",
            'route_number': 'TEST-SQL'
        },
        'xss_attack': {
            'name': '<script>alert("xss")</script>',
            'route_number': 'TEST-XSS'
        },
        'too_long_name': {
            'name': 'A' * 300,  # Превышает лимит в 200 символов
            'route_number': 'TEST-LONG'
        },
        'negative_duration': {
            'name': 'Test Route',
            'route_number': 'TEST-NEG',
            'estimated_duration': -10.0
        },
        'invalid_status': {
            'name': 'Test Route', 
            'route_number': 'TEST-STATUS',
            'status': 'invalid_status'
        },
        'invalid_complexity': {
            'name': 'Test Route',
            'route_number': 'TEST-COMPLEX', 
            'complexity_level': 'extreme'
        }
    } 