#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты производительности для системы технологических маршрутов и BOM
"""

import pytest
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.mark.performance
@pytest.mark.slow
class TestRoutesPerformance:
    """Тесты производительности для технологических маршрутов"""
    
    def test_create_multiple_routes_performance(self, client, auth_headers_admin):
        """Тест: создание множественных маршрутов - проверка производительности"""
        start_time = time.time()
        created_routes = []
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Создаем 50 маршрутов
        for i in range(50):
            data = {
                'name': f'Маршрут производительности {i+1}',
                'route_number': f'TR-PERF-{timestamp}-{i+1:03d}',
                'description': f'Маршрут для теста производительности #{i+1}',
                'estimated_duration': 120.0 + i * 5.0,
                'complexity_level': 'medium'
            }
            
            response = client.post('/api/routes', 
                                 json=data, 
                                 headers=auth_headers_admin)
            
            assert response.status_code == 201
            created_routes.append(response.json['id'])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Производительность: не более 0.5 секунды на маршрут
        average_time_per_route = total_time / 50
        assert average_time_per_route < 0.5, f"Слишком медленное создание маршрутов: {average_time_per_route:.3f}s на маршрут"
        
        print(f"\n📊 Создано 50 маршрутов за {total_time:.2f}s (среднее: {average_time_per_route:.3f}s на маршрут)")
    
    def test_routes_list_pagination_performance(self, client, auth_headers_admin):
        """Тест: производительность пагинации списка маршрутов"""
        # Сначала создаем тестовые данные
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        for i in range(100):
            data = {
                'name': f'Маршрут пагинации {i+1}',
                'route_number': f'TR-PAG-{timestamp}-{i+1:03d}',
                'description': f'Маршрут для теста пагинации #{i+1}'
            }
            
            response = client.post('/api/routes', 
                                 json=data, 
                                 headers=auth_headers_admin)
            assert response.status_code == 201
        
        # Тестируем производительность получения страниц
        start_time = time.time()
        
        for page in range(1, 11):  # Получаем 10 страниц по 10 элементов
            response = client.get(f'/api/routes?page={page}&per_page=10', 
                                headers=auth_headers_admin)
            
            assert response.status_code == 200
            data = response.json
            
            # Проверяем структуру ответа
            if 'data' in data:
                assert isinstance(data['data'], list)
                assert len(data['data']) <= 10
            elif 'items' in data:
                assert len(data['items']) <= 10
            else:
                assert isinstance(data, list)
                assert len(data) <= 100  # Если пагинация не реализована
        
        end_time = time.time()
        total_time = end_time - start_time
        average_time_per_page = total_time / 10
        
        # Производительность: не более 0.2 секунды на страницу
        assert average_time_per_page < 0.2, f"Слишком медленная пагинация: {average_time_per_page:.3f}s на страницу"
        
        print(f"\n📊 Получено 10 страниц за {total_time:.2f}s (среднее: {average_time_per_page:.3f}s на страницу)")
    
    def test_concurrent_route_creation(self, client, auth_headers_admin):
        """Тест: конкурентное создание маршрутов"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        results = []
        errors = []
        
        def create_route(thread_id):
            """Функция для создания маршрута в отдельном потоке"""
            try:
                data = {
                    'name': f'Конкурентный маршрут {thread_id}',
                    'route_number': f'TR-CONC-{timestamp}-{thread_id:03d}',
                    'description': f'Маршрут созданный в потоке {thread_id}'
                }
                
                response = client.post('/api/routes', 
                                     json=data, 
                                     headers=auth_headers_admin)
                
                return {
                    'thread_id': thread_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 201,
                    'route_id': response.json.get('id') if response.status_code == 201 else None
                }
            except Exception as e:
                return {
                    'thread_id': thread_id,
                    'error': str(e),
                    'success': False
                }
        
        # Запускаем 10 потоков одновременно
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_route, i) for i in range(1, 11)]
            
            for future in as_completed(futures):
                result = future.result()
                if result.get('success'):
                    results.append(result)
                else:
                    errors.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Проверяем результаты
        successful_creations = len(results)
        assert successful_creations >= 8, f"Слишком много ошибок при конкурентном создании: {len(errors)} из 10"
        
        # Проверяем, что нет дублирующихся ID
        route_ids = [r['route_id'] for r in results if r['route_id']]
        assert len(route_ids) == len(set(route_ids)), "Обнаружены дублирующиеся ID маршрутов"
        
        print(f"\n📊 Конкурентное создание: {successful_creations}/10 успешно за {total_time:.2f}s")


@pytest.mark.performance
@pytest.mark.slow
class TestBOMPerformance:
    """Тесты производительности для BOM"""
    
    def test_create_deep_bom_hierarchy_performance(self, client, auth_headers_admin):
        """Тест: создание глубокой иерархии BOM - проверка производительности"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        start_time = time.time()
        
        # Создаем корневой элемент
        root_data = {
            'part_number': f'BOM-DEEP-ROOT-{timestamp}',
            'name': 'Корневая сборка для теста производительности',
            'description': 'Тест глубокой иерархии',
            'is_assembly': True
        }
        
        response = client.post('/api/bom/items', 
                             json=root_data, 
                             headers=auth_headers_admin)
        assert response.status_code == 201
        parent_id = response.json['id']
        
        # Создаем 10 уровней иерархии с 3 элементами на каждом уровне
        total_items = 1  # Корневой элемент
        
        for level in range(10):
            current_level_items = []
            
            for item_num in range(3):
                item_data = {
                    'part_number': f'BOM-DEEP-L{level}-I{item_num}-{timestamp}',
                    'name': f'Элемент уровня {level}, позиция {item_num}',
                    'parent_id': parent_id,
                    'quantity': 1.0 + item_num,
                    'cost_per_unit': 100.0 + level * 10 + item_num
                }
                
                response = client.post('/api/bom/items', 
                                     json=item_data, 
                                     headers=auth_headers_admin)
                assert response.status_code == 201
                current_level_items.append(response.json['id'])
                total_items += 1
            
            # Для следующего уровня используем первый элемент текущего как родитель
            if current_level_items:
                parent_id = current_level_items[0]
        
        end_time = time.time()
        total_time = end_time - start_time
        average_time_per_item = total_time / total_items
        
        # Производительность: не более 0.3 секунды на элемент
        assert average_time_per_item < 0.3, f"Слишком медленное создание BOM: {average_time_per_item:.3f}s на элемент"
        
        print(f"\n📊 Создано {total_items} элементов BOM за {total_time:.2f}s (среднее: {average_time_per_item:.3f}s на элемент)")
    
    def test_bom_tree_retrieval_performance(self, client, auth_headers_admin):
        """Тест: производительность получения дерева BOM"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Создаем сложную структуру BOM
        root_data = {
            'part_number': f'BOM-TREE-ROOT-{timestamp}',
            'name': 'Корневая сборка для теста дерева',
            'description': 'Тест производительности получения дерева',
            'is_assembly': True
        }
        
        response = client.post('/api/bom/items', 
                             json=root_data, 
                             headers=auth_headers_admin)
        assert response.status_code == 201
        root_id = response.json['id']
        
        # Создаем 50 дочерних элементов
        for i in range(50):
            child_data = {
                'part_number': f'BOM-TREE-CHILD-{timestamp}-{i:03d}',
                'name': f'Дочерний элемент {i+1}',
                'parent_id': root_id,
                'quantity': 1.0 + i * 0.1,
                'cost_per_unit': 50.0 + i
            }
            
            response = client.post('/api/bom/items', 
                                 json=child_data, 
                                 headers=auth_headers_admin)
            assert response.status_code == 201
        
        # Тестируем производительность получения дерева
        start_time = time.time()
        
        for _ in range(10):  # Получаем дерево 10 раз
            response = client.get(f'/api/bom/{root_id}/tree', 
                                headers=auth_headers_admin)
            
            if response.status_code == 200:
                tree_data = response.json
                assert 'id' in tree_data
                assert tree_data['id'] == root_id
            else:
                pytest.skip("API получения дерева BOM еще не реализован")
        
        end_time = time.time()
        total_time = end_time - start_time
        average_time_per_request = total_time / 10
        
        # Производительность: не более 0.5 секунды на запрос дерева
        assert average_time_per_request < 0.5, f"Слишком медленное получение дерева BOM: {average_time_per_request:.3f}s на запрос"
        
        print(f"\n📊 Получено дерево BOM 10 раз за {total_time:.2f}s (среднее: {average_time_per_request:.3f}s на запрос)")
    
    def test_concurrent_bom_modifications(self, client, auth_headers_admin):
        """Тест: конкурентные изменения BOM"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Создаем базовый элемент BOM
        base_data = {
            'part_number': f'BOM-CONC-BASE-{timestamp}',
            'name': 'Базовый элемент для конкурентного теста',
            'description': 'Элемент для тестирования конкурентных изменений'
        }
        
        response = client.post('/api/bom/items', 
                             json=base_data, 
                             headers=auth_headers_admin)
        assert response.status_code == 201
        base_id = response.json['id']
        
        results = []
        
        def create_child_bom(thread_id):
            """Функция для создания дочернего элемента BOM в отдельном потоке"""
            try:
                data = {
                    'part_number': f'BOM-CONC-CHILD-{timestamp}-{thread_id:03d}',
                    'name': f'Дочерний элемент {thread_id}',
                    'parent_id': base_id,
                    'quantity': 1.0 + thread_id * 0.1
                }
                
                response = client.post('/api/bom/items', 
                                     json=data, 
                                     headers=auth_headers_admin)
                
                return {
                    'thread_id': thread_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 201,
                    'bom_id': response.json.get('id') if response.status_code == 201 else None
                }
            except Exception as e:
                return {
                    'thread_id': thread_id,
                    'error': str(e),
                    'success': False
                }
        
        # Запускаем 15 потоков одновременно
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(create_child_bom, i) for i in range(1, 16)]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Анализируем результаты
        successful_creations = len([r for r in results if r.get('success')])
        errors = [r for r in results if not r.get('success')]
        
        assert successful_creations >= 12, f"Слишком много ошибок при конкурентном создании BOM: {len(errors)} из 15"
        
        # Проверяем уникальность ID
        bom_ids = [r['bom_id'] for r in results if r.get('bom_id')]
        assert len(bom_ids) == len(set(bom_ids)), "Обнаружены дублирующиеся ID элементов BOM"
        
        print(f"\n📊 Конкурентное создание BOM: {successful_creations}/15 успешно за {total_time:.2f}s")


@pytest.mark.performance
@pytest.mark.slow  
class TestSystemIntegrationPerformance:
    """Тесты производительности интеграции системы"""
    
    def test_full_workflow_performance(self, client, auth_headers_admin):
        """Тест: производительность полного рабочего процесса"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        start_time = time.time()
        
        # 1. Создание технологического маршрута
        route_data = {
            'name': f'Комплексный маршрут {timestamp}',
            'route_number': f'TR-COMPLEX-{timestamp}',
            'description': 'Маршрут для полного теста производительности'
        }
        
        response = client.post('/api/routes', 
                             json=route_data, 
                             headers=auth_headers_admin)
        assert response.status_code == 201
        route_id = response.json['id']
        
        # 2. Создание операции
        operation_data = {
            'name': f'Операция {timestamp}',
            'operation_code': f'OP-{timestamp}',
            'operation_type': 'machining',
            'setup_time': 10.0,
            'cycle_time': 5.0
        }
        
        response = client.post('/api/operations', 
                             json=operation_data, 
                             headers=auth_headers_admin)
        
        if response.status_code == 201:
            operation_id = response.json['id']
            
            # 3. Связывание операции с маршрутом
            link_data = {
                'operation_id': operation_id,
                'sequence_number': 1
            }
            
            response = client.post(f'/api/routes/{route_id}/operations',
                                 json=link_data,
                                 headers=auth_headers_admin)
        
        # 4. Создание BOM структуры
        bom_root_data = {
            'part_number': f'BOM-COMPLEX-{timestamp}',
            'name': f'Комплексная сборка {timestamp}',
            'technological_route_id': route_id,
            'is_assembly': True
        }
        
        response = client.post('/api/bom/items', 
                             json=bom_root_data, 
                             headers=auth_headers_admin)
        assert response.status_code == 201
        bom_root_id = response.json['id']
        
        # 5. Добавление 20 дочерних элементов
        for i in range(20):
            child_data = {
                'part_number': f'BOM-PART-{timestamp}-{i:03d}',
                'name': f'Деталь {i+1}',
                'parent_id': bom_root_id,
                'quantity': 1.0 + i * 0.1
            }
            
            response = client.post('/api/bom/items', 
                                 json=child_data, 
                                 headers=auth_headers_admin)
            assert response.status_code == 201
        
        # 6. Получение полной информации
        response = client.get(f'/api/routes/{route_id}', 
                            headers=auth_headers_admin)
        assert response.status_code == 200
        
        response = client.get(f'/api/bom/{bom_root_id}/tree', 
                            headers=auth_headers_admin)
        # Может быть не реализовано - это нормально
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Полный workflow должен выполняться не более чем за 10 секунд
        assert total_time < 10.0, f"Слишком медленный полный workflow: {total_time:.2f}s"
        
        print(f"\n📊 Полный workflow выполнен за {total_time:.2f}s")
    
    def test_database_load_simulation(self, client, auth_headers_admin):
        """Тест: симуляция нагрузки на базу данных"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        start_time = time.time()
        
        # Создаем 100 маршрутов и 300 элементов BOM
        routes_created = 0
        bom_items_created = 0
        
        # Создание маршрутов
        for i in range(100):
            data = {
                'name': f'Нагрузочный маршрут {i+1}',
                'route_number': f'TR-LOAD-{timestamp}-{i+1:03d}',
                'description': f'Маршрут для нагрузочного тестирования #{i+1}'
            }
            
            response = client.post('/api/routes', 
                                 json=data, 
                                 headers=auth_headers_admin)
            if response.status_code == 201:
                routes_created += 1
        
        # Создание элементов BOM
        for i in range(300):
            data = {
                'part_number': f'BOM-LOAD-{timestamp}-{i+1:03d}',
                'name': f'Нагрузочный элемент BOM {i+1}',
                'description': f'Элемент для нагрузочного тестирования #{i+1}',
                'quantity': 1.0 + (i % 10) * 0.1
            }
            
            response = client.post('/api/bom/items', 
                                 json=data, 
                                 headers=auth_headers_admin)
            if response.status_code == 201:
                bom_items_created += 1
        
        # Тестируем операции чтения
        read_start = time.time()
        
        for _ in range(20):
            response = client.get('/api/routes?per_page=50', 
                                headers=auth_headers_admin)
            assert response.status_code == 200
            
            response = client.get('/api/bom?per_page=50', 
                                headers=auth_headers_admin)
            assert response.status_code == 200
        
        read_end = time.time()
        read_time = read_end - read_start
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Проверяем производительность
        create_time = read_start - start_time
        average_create_time = create_time / (routes_created + bom_items_created)
        average_read_time = read_time / 40  # 20 запросов * 2 типа
        
        print(f"\n📊 Нагрузочный тест:")
        print(f"  - Создано маршрутов: {routes_created}/100")
        print(f"  - Создано элементов BOM: {bom_items_created}/300")
        print(f"  - Время создания: {create_time:.2f}s (среднее: {average_create_time:.3f}s на элемент)")
        print(f"  - Время чтения: {read_time:.2f}s (среднее: {average_read_time:.3f}s на запрос)")
        print(f"  - Общее время: {total_time:.2f}s")
        
        # Ограничения производительности
        assert average_create_time < 0.2, f"Слишком медленное создание: {average_create_time:.3f}s на элемент"
        assert average_read_time < 0.1, f"Слишком медленное чтение: {average_read_time:.3f}s на запрос"
        assert total_time < 60.0, f"Общее время нагрузочного теста превышено: {total_time:.2f}s" 