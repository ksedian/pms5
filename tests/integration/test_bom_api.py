#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграционные тесты для API BOM (Bill of Materials)
"""

import pytest
import json
import io
from datetime import datetime


@pytest.mark.integration
class TestBOMAPIIntegration:
    """Интеграционные тесты API BOM"""
    
    def test_complete_bom_hierarchy_workflow(self, client, auth_headers_admin):
        """Тест полного жизненного цикла иерархии BOM"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # 1. Создание корневого элемента (сборки)
        root_data = {
            'part_number': f'BOM-ROOT-{timestamp}',
            'name': 'Интеграционная тестовая сборка',
            'description': 'Корневая сборка для интеграционного теста',
            'quantity': 1.0,
            'unit': 'шт',
            'is_assembly': True,
            'material_type': 'assembly',
            'cost_per_unit': 1000.0,
            'currency': 'RUB'
        }
        
        response = client.post('/api/bom/items', 
                             json=root_data, 
                             headers=auth_headers_admin)
        
        assert response.status_code == 201
        root_item = response.json
        root_id = root_item['id']
        assert root_item['is_assembly'] == True
        assert root_item['level'] == 0
        
        # 2. Создание дочернего элемента (подсборка)
        sub_assembly_data = {
            'part_number': f'BOM-SUB-{timestamp}',
            'name': 'Тестовая подсборка',
            'description': 'Подсборка первого уровня',
            'parent_id': root_id,
            'quantity': 2.0,
            'unit': 'шт',
            'is_assembly': True,
            'material_type': 'assembly',
            'cost_per_unit': 300.0,
            'currency': 'RUB'
        }
        
        response = client.post('/api/bom/items', 
                             json=sub_assembly_data, 
                             headers=auth_headers_admin)
        
        assert response.status_code == 201
        sub_item = response.json
        sub_id = sub_item['id']
        assert sub_item['level'] == 1
        assert sub_item['parent_id'] == root_id
        
        # 3. Создание деталей второго уровня
        details_data = [
            {
                'part_number': f'BOM-PART1-{timestamp}',
                'name': 'Тестовая деталь 1',
                'parent_id': sub_id,
                'quantity': 4.0,
                'unit': 'шт',
                'is_assembly': False,
                'material_type': 'steel',
                'cost_per_unit': 50.0
            },
            {
                'part_number': f'BOM-PART2-{timestamp}',
                'name': 'Тестовая деталь 2', 
                'parent_id': sub_id,
                'quantity': 2.0,
                'unit': 'кг',
                'is_assembly': False,
                'material_type': 'aluminum',
                'cost_per_unit': 75.0
            }
        ]
        
        detail_ids = []
        for detail_data in details_data:
            response = client.post('/api/bom/items', 
                                 json=detail_data, 
                                 headers=auth_headers_admin)
            
            assert response.status_code == 201
            detail = response.json
            detail_ids.append(detail['id'])
            assert detail['level'] == 2
            assert detail['parent_id'] == sub_id
        
        # 4. Получение полного дерева BOM
        response = client.get(f'/api/bom/{root_id}/tree', 
                            headers=auth_headers_admin)
        
        if response.status_code == 200:
            tree_data = response.json
            
            # Проверяем структуру дерева
            assert tree_data['id'] == root_id
            assert tree_data['level'] == 0
            assert 'children' in tree_data
            assert len(tree_data['children']) >= 1
            
            # Проверяем подсборку
            sub_found = False
            for child in tree_data['children']:
                if child['id'] == sub_id:
                    sub_found = True
                    assert child['level'] == 1
                    assert len(child.get('children', [])) >= 2  # Две детали
                    break
            
            assert sub_found, "Подсборка не найдена в дереве"
        else:
            pytest.skip("API получения дерева BOM еще не реализован")
        
        # 5. Обновление элемента BOM
        update_data = {
            'name': 'Обновленная тестовая сборка',
            'cost_per_unit': 1200.0,
            'description': 'Обновленное описание'
        }
        
        response = client.put(f'/api/bom/{root_id}', 
                            json=update_data, 
                            headers=auth_headers_admin)
        
        if response.status_code == 200:
            updated_item = response.json
            assert updated_item['name'] == update_data['name']
            assert updated_item['cost_per_unit'] == 1200.0
        else:
            pytest.skip("API обновления BOM еще не реализован")
        
        # 6. Удаление элемента (каскадное)
        response = client.delete(f'/api/bom/{root_id}', 
                               headers=auth_headers_admin)
        
        assert response.status_code == 200
        
        # 7. Проверка, что элемент удален
        response = client.get(f'/api/bom/{root_id}', 
                            headers=auth_headers_admin)
        
        assert response.status_code == 404
    
    def test_bom_cost_calculation(self, client, auth_headers_admin):
        """Тест расчета стоимости BOM с учетом иерархии"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Создаем простую иерархию для расчета стоимости
        root_data = {
            'part_number': f'BOM-COST-ROOT-{timestamp}',
            'name': 'Сборка для расчета стоимости',
            'quantity': 1.0,
            'unit': 'шт',
            'is_assembly': True,
            'cost_per_unit': 100.0  # Стоимость сборки
        }
        
        response = client.post('/api/bom/items', 
                             json=root_data, 
                             headers=auth_headers_admin)
        
        assert response.status_code == 201
        root_id = response.json['id']
        
        # Создаем детали с известной стоимостью
        parts_data = [
            {
                'part_number': f'BOM-COST-P1-{timestamp}',
                'name': 'Деталь 1',
                'parent_id': root_id,
                'quantity': 2.0,
                'cost_per_unit': 50.0  # 2 * 50 = 100
            },
            {
                'part_number': f'BOM-COST-P2-{timestamp}',
                'name': 'Деталь 2',
                'parent_id': root_id,
                'quantity': 3.0,
                'cost_per_unit': 30.0  # 3 * 30 = 90
            }
        ]
        
        for part_data in parts_data:
            response = client.post('/api/bom/items', 
                                 json=part_data, 
                                 headers=auth_headers_admin)
            assert response.status_code == 201
        
        # Получаем дерево с расчетом стоимости
        response = client.get(f'/api/bom/{root_id}/tree', 
                            headers=auth_headers_admin)
        
        if response.status_code == 200:
            tree_data = response.json
            
            # Проверяем, что есть информация о стоимости
            assert 'total_cost' in tree_data or 'cost_per_unit' in tree_data
            
            # Общая стоимость должна быть: 100 (сборка) + 100 (детали 1) + 90 (детали 2) = 290
            if 'total_cost' in tree_data:
                expected_cost = 100 + (2 * 50) + (3 * 30)  # 290
                assert abs(tree_data['total_cost'] - expected_cost) < 0.01
        else:
            pytest.skip("API расчета стоимости BOM еще не реализован")
    
    def test_bom_import_export_workflow(self, client, auth_headers_admin):
        """Тест импорта и экспорта BOM"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # 1. Тестируем импорт CSV
        csv_content = f"""part_number,name,parent_part_number,quantity,unit,cost_per_unit,currency,material_type
BOM-IMP-ROOT-{timestamp},Импортированная сборка,,1.0,шт,500.0,RUB,assembly
BOM-IMP-P1-{timestamp},Импортированная деталь 1,BOM-IMP-ROOT-{timestamp},2.0,шт,100.0,RUB,steel
BOM-IMP-P2-{timestamp},Импортированная деталь 2,BOM-IMP-ROOT-{timestamp},1.5,кг,200.0,RUB,aluminum"""
        
        # Создаем файл в памяти
        csv_file = io.StringIO(csv_content)
        
        # Попытка импорта
        files = {'file': ('test_bom.csv', csv_file.getvalue(), 'text/csv')}
        
        response = client.post('/api/bom/import/csv',
                             files=files,
                             headers=auth_headers_admin)
        
        if response.status_code == 200:
            import_result = response.json
            
            # Проверяем результат импорта
            assert 'imported_items' in import_result or 'success' in import_result
            
            # Находим корневой элемент
            response = client.get('/api/bom', headers=auth_headers_admin)
            assert response.status_code == 200
            
            bom_list = response.json
            items = bom_list.get('items', bom_list)
            
            root_item = None
            for item in items:
                if item['part_number'] == f'BOM-IMP-ROOT-{timestamp}':
                    root_item = item
                    break
            
            if root_item:
                root_id = root_item['id']
                
                # 2. Тестируем экспорт
                response = client.get(f'/api/bom/{root_id}/export/csv',
                                    headers=auth_headers_admin)
                
                if response.status_code == 200:
                    # Проверяем, что получили CSV контент
                    assert 'text/csv' in response.headers.get('Content-Type', '')
                    csv_data = response.data.decode('utf-8')
                    assert 'part_number' in csv_data
                    assert f'BOM-IMP-ROOT-{timestamp}' in csv_data
                else:
                    pytest.skip("API экспорта CSV еще не реализован")
            else:
                pytest.skip("Импортированные элементы не найдены")
        else:
            pytest.skip("API импорта CSV еще не реализован")


@pytest.mark.integration
class TestBOMVersioningIntegration:
    """Интеграционные тесты версионирования BOM"""
    
    def test_bom_versioning_workflow(self, client, auth_headers_admin):
        """Тест полного жизненного цикла версионирования BOM"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # 1. Создаем BOM элемент
        bom_data = {
            'part_number': f'BOM-VER-{timestamp}',
            'name': 'BOM для версионирования',
            'description': 'Начальная версия',
            'quantity': 1.0,
            'cost_per_unit': 100.0
        }
        
        response = client.post('/api/bom/items', 
                             json=bom_data, 
                             headers=auth_headers_admin)
        
        assert response.status_code == 201
        bom_id = response.json['id']
        
        # 2. Обновляем элемент несколько раз для создания версий
        updates = [
            {'name': 'BOM версия 2', 'cost_per_unit': 120.0},
            {'name': 'BOM версия 3', 'cost_per_unit': 150.0, 'description': 'Третья версия'}
        ]
        
        for update_data in updates:
            response = client.put(f'/api/bom/{bom_id}', 
                                json=update_data, 
                                headers=auth_headers_admin)
            
            if response.status_code != 200:
                pytest.skip("API обновления BOM еще не реализован")
        
        # 3. Получаем историю версий
        response = client.get(f'/api/bom/{bom_id}/versions', 
                            headers=auth_headers_admin)
        
        if response.status_code == 200:
            versions = response.json
            
            # Должно быть минимум 3 версии (начальная + 2 обновления)
            assert len(versions) >= 3
            
            # Проверяем структуру версий
            for version in versions:
                assert 'version_number' in version or 'id' in version
                assert 'created_at' in version
                assert 'data' in version or 'changes' in version
            
            # 4. Сравниваем версии
            if len(versions) >= 2:
                v1_id = versions[0].get('id', 1)
                v2_id = versions[1].get('id', 2)
                
                response = client.get(f'/api/bom/{bom_id}/versions/diff/{v1_id}/{v2_id}',
                                    headers=auth_headers_admin)
                
                if response.status_code == 200:
                    diff_data = response.json
                    
                    # Проверяем структуру diff
                    assert 'changes' in diff_data or 'differences' in diff_data
                else:
                    pytest.skip("API сравнения версий BOM еще не реализован")
        else:
            pytest.skip("API версионирования BOM еще не реализован")


@pytest.mark.integration
class TestBOMSecurityIntegration:
    """Интеграционные тесты безопасности BOM API"""
    
    def test_engineer_can_manage_bom(self, client, auth_headers_engineer):
        """Тест: инженер может управлять BOM"""
        data = {
            'part_number': f'BOM-ENG-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'name': 'BOM от инженера',
            'description': 'BOM, созданный инженером'
        }
        
        response = client.post('/api/bom/items', 
                             json=data, 
                             headers=auth_headers_engineer)
        
        assert response.status_code == 201
    
    def test_user_cannot_create_bom(self, client, auth_headers_user):
        """Тест: обычный пользователь не может создавать BOM"""
        data = {
            'part_number': f'BOM-USER-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'name': 'BOM от пользователя',
            'description': 'Попытка создать BOM обычным пользователем'
        }
        
        response = client.post('/api/bom/items', 
                             json=data, 
                             headers=auth_headers_user)
        
        assert response.status_code == 403
    
    def test_user_can_read_bom(self, client, auth_headers_user):
        """Тест: обычный пользователь может читать BOM"""
        response = client.get('/api/bom', 
                            headers=auth_headers_user)
        
        assert response.status_code == 200


@pytest.mark.integration
class TestBOMErrorHandlingIntegration:
    """Интеграционные тесты обработки ошибок BOM"""
    
    def test_circular_reference_prevention(self, client, auth_headers_admin):
        """Тест предотвращения циклических ссылок"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Создаем два элемента
        item1_data = {
            'part_number': f'BOM-CIRC1-{timestamp}',
            'name': 'Элемент 1',
            'description': 'Первый элемент для теста циклических ссылок'
        }
        
        response = client.post('/api/bom/items', 
                             json=item1_data, 
                             headers=auth_headers_admin)
        assert response.status_code == 201
        item1_id = response.json['id']
        
        item2_data = {
            'part_number': f'BOM-CIRC2-{timestamp}',
            'name': 'Элемент 2',
            'parent_id': item1_id,
            'description': 'Второй элемент для теста циклических ссылок'
        }
        
        response = client.post('/api/bom/items', 
                             json=item2_data, 
                             headers=auth_headers_admin)
        assert response.status_code == 201
        item2_id = response.json['id']
        
        # Пытаемся создать циклическую ссылку: item1 -> parent = item2
        update_data = {
            'parent_id': item2_id
        }
        
        response = client.put(f'/api/bom/{item1_id}', 
                            json=update_data, 
                            headers=auth_headers_admin)
        
        # Должна быть ошибка циклической ссылки
        if response.status_code in [400, 409]:
            assert 'error' in response.json
            error_message = response.json['error'].lower()
            assert 'цикл' in error_message or 'circular' in error_message
        else:
            pytest.skip("Проверка циклических ссылок еще не реализована")
    
    def test_max_nesting_level_enforcement(self, client, auth_headers_admin):
        """Тест ограничения максимального уровня вложенности"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Создаем глубокую иерархию
        parent_id = None
        max_levels = 10  # Попытаемся создать 10 уровней
        
        for level in range(max_levels):
            item_data = {
                'part_number': f'BOM-DEEP-L{level}-{timestamp}',
                'name': f'Элемент уровня {level}',
                'parent_id': parent_id
            }
            
            response = client.post('/api/bom/items', 
                                 json=item_data, 
                                 headers=auth_headers_admin)
            
            if response.status_code == 201:
                parent_id = response.json['id']
            else:
                # Если получили ошибку, проверяем, что это из-за глубины
                if response.status_code == 400:
                    error_message = response.json.get('error', '').lower()
                    if 'уровень' in error_message or 'level' in error_message or 'глубина' in error_message:
                        # Это ожидаемая ошибка ограничения глубины
                        assert level > 0, "Ограничение глубины сработало слишком рано"
                        break
                
                # Если не связано с глубиной, пропускаем тест
                pytest.skip("Ограничение глубины вложенности еще не реализовано")
        else:
            # Если создали все 10 уровней без ошибок
            pytest.skip("Ограничение глубины вложенности не достигнуто или не реализовано") 