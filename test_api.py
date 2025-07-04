#!/usr/bin/env python3
"""
Скрипт для тестирования API технологических маршрутов и BOM
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_login():
    """Тестируем логин и получаем токен"""
    print("🔐 Тестируем авторизацию...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        print("✅ Авторизация успешна!")
        return token
    else:
        print(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
        return None

def test_routes_api(token):
    """Тестируем API технологических маршрутов"""
    print("\n🛣️ Тестируем API технологических маршрутов...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Создание нового маршрута
    print("📝 Создаем новый технологический маршрут...")
    route_data = {
        "name": "Тестовый маршрут изготовления детали",
        "route_number": f"TR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "description": "Автоматически созданный тестовый маршрут",
        "status": "draft",
        "estimated_duration": 120,
        "complexity_level": "medium"
    }
    
    response = requests.post(f"{BASE_URL}/api/routes", json=route_data, headers=headers)
    
    if response.status_code == 201:
        route = response.json()
        route_id = route['id']
        print(f"✅ Маршрут создан! ID: {route_id}, Название: {route['name']}")
        
        # 2. Получение маршрута по ID
        print(f"📖 Получаем маршрут по ID {route_id}...")
        response = requests.get(f"{BASE_URL}/api/routes/{route_id}", headers=headers)
        
        if response.status_code == 200:
            print("✅ Маршрут успешно получен!")
        else:
            print(f"❌ Ошибка получения маршрута: {response.status_code}")
        
        # 3. Обновление маршрута
        print(f"✏️ Обновляем маршрут {route_id}...")
        update_data = {
            "description": "Обновленное описание тестового маршрута",
            "status": "active"
        }
        
        response = requests.put(f"{BASE_URL}/api/routes/{route_id}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            print("✅ Маршрут успешно обновлен!")
        else:
            print(f"❌ Ошибка обновления маршрута: {response.status_code}")
        
        return route_id
    else:
        print(f"❌ Ошибка создания маршрута: {response.status_code} - {response.text}")
        return None

def test_operations_api(token):
    """Тестируем API операций"""
    print("\n⚙️ Тестируем API операций...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Создание новой операции
    print("📝 Создаем новую операцию...")
    operation_data = {
        "name": "Тестовая операция фрезерования",
        "operation_code": f"OP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "operation_type": "machining",
        "description": "Автоматически созданная тестовая операция",
        "setup_time": 30,
        "operation_time": 60
    }
    
    response = requests.post(f"{BASE_URL}/api/operations", json=operation_data, headers=headers)
    
    if response.status_code == 201:
        operation = response.json()
        operation_id = operation['id']
        print(f"✅ Операция создана! ID: {operation_id}, Название: {operation['name']}")
        return operation_id
    else:
        print(f"❌ Ошибка создания операции: {response.status_code} - {response.text}")
        return None

def test_bom_api(token):
    """Тестируем API BOM"""
    print("\n📋 Тестируем API BOM...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Создание корневого элемента BOM
    print("📝 Создаем корневой элемент BOM...")
    bom_data = {
        "part_number": f"BOM-ROOT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "name": "Тестовая сборка",
        "description": "Автоматически созданный тестовый элемент BOM",
        "quantity": 1.0,
        "unit": "шт",
        "is_assembly": True,
        "status": "active",
        "material_type": "assembly",
        "cost_per_unit": 1000.0,
        "currency": "RUB"
    }
    
    response = requests.post(f"{BASE_URL}/api/bom/items", json=bom_data, headers=headers)
    
    if response.status_code == 201:
        bom_item = response.json()
        bom_id = bom_item['id']
        print(f"✅ Элемент BOM создан! ID: {bom_id}, Деталь: {bom_item['part_number']}")
        
        # 2. Создание дочернего элемента
        print(f"📝 Создаем дочерний элемент для BOM {bom_id}...")
        child_data = {
            "part_number": f"BOM-CHILD-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "name": "Тестовая деталь",
            "description": "Дочерний элемент BOM",
            "parent_id": bom_id,
            "quantity": 2.0,
            "unit": "шт",
            "is_assembly": False,
            "material_type": "steel",
            "cost_per_unit": 150.0
        }
        
        response = requests.post(f"{BASE_URL}/api/bom/items", json=child_data, headers=headers)
        
        if response.status_code == 201:
            child_item = response.json()
            print(f"✅ Дочерний элемент создан! ID: {child_item['id']}")
        else:
            print(f"❌ Ошибка создания дочернего элемента: {response.status_code}")
        
        # 3. Получение структуры BOM
        print("📖 Получаем структуру BOM...")
        response = requests.get(f"{BASE_URL}/api/bom", headers=headers)
        
        if response.status_code == 200:
            bom_tree = response.json()
            print(f"✅ Структура BOM получена! Всего элементов: {bom_tree['total_items']}")
        else:
            print(f"❌ Ошибка получения структуры BOM: {response.status_code}")
        
        return bom_id
    else:
        print(f"❌ Ошибка создания элемента BOM: {response.status_code} - {response.text}")
        return None

def test_list_apis(token):
    """Тестируем API списков"""
    print("\n📋 Тестируем получение списков...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Получение списка маршрутов
    print("📖 Получаем список маршрутов...")
    response = requests.get(f"{BASE_URL}/api/routes", headers=headers)
    
    if response.status_code == 200:
        routes = response.json()
        print(f"✅ Получено маршрутов: {routes.get('total', 0)}")
    else:
        print(f"❌ Ошибка получения списка маршрутов: {response.status_code}")
    
    # Получение списка операций
    print("📖 Получаем список операций...")
    response = requests.get(f"{BASE_URL}/api/operations", headers=headers)
    
    if response.status_code == 200:
        operations = response.json()
        print(f"✅ Получено операций: {operations.get('total', 0)}")
    else:
        print(f"❌ Ошибка получения списка операций: {response.status_code}")

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования API технологических маршрутов и BOM")
    print("=" * 60)
    
    # 1. Авторизация
    token = test_login()
    if not token:
        print("❌ Не удалось получить токен авторизации. Прекращаем тестирование.")
        return
    
    # 2. Тестирование API
    route_id = test_routes_api(token)
    operation_id = test_operations_api(token)
    bom_id = test_bom_api(token)
    test_list_apis(token)
    
    print("\n" + "=" * 60)
    print("🎉 Тестирование завершено!")
    print(f"Созданные объекты:")
    if route_id:
        print(f"  - Маршрут ID: {route_id}")
    if operation_id:
        print(f"  - Операция ID: {operation_id}")
    if bom_id:
        print(f"  - Элемент BOM ID: {bom_id}")

if __name__ == "__main__":
    main() 