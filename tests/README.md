# Тестовая инфраструктура для системы технологических маршрутов и BOM

## Обзор

Эта тестовая инфраструктура предоставляет комплексные тесты для функциональности управления технологическими маршрутами и спецификациями материалов (BOM) в MES системе. Тесты разделены на несколько категорий для эффективной организации и выполнения.

## Структура тестов

```
tests/
├── conftest.py              # Fixtures и конфигурация pytest
├── pytest.ini              # Конфигурация pytest, маркеры
├── unit/                    # Unit тесты
│   └── test_models.py       # Тесты моделей данных
├── integration/             # Интеграционные тесты
│   ├── test_routes_api.py   # API технологических маршрутов
│   └── test_bom_api.py      # API управления BOM
├── error/                   # Негативные тесты
│   ├── test_routes_errors.py # Обработка ошибок маршрутов
│   └── test_bom_errors.py   # Обработка ошибок BOM
├── performance/             # Тесты производительности
│   └── test_load.py         # Нагрузочные тесты
└── README.md               # Эта документация
```

## Категории тестов

### 1. Unit тесты (`unit/`)

Тестируют отдельные компоненты системы в изоляции:

- **Модели данных**: валидация, методы, отношения
- **Утилиты**: вспомогательные функции
- **Сервисы**: бизнес-логика

**Запуск unit тестов:**
```bash
pytest tests/unit/ -v
pytest -m unit
```

### 2. Интеграционные тесты (`integration/`)

Тестируют взаимодействие между компонентами:

- **API endpoints**: CRUD операции, фильтрация, пагинация
- **База данных**: транзакции, ограничения
- **Авторизация**: проверка прав доступа

**Запуск интеграционных тестов:**
```bash
pytest tests/integration/ -v
pytest -m integration
```

### 3. Негативные тесты (`error/`)

Проверяют обработку ошибочных ситуаций:

- **Валидация данных**: некорректные форматы, отсутствующие поля
- **Безопасность**: SQL инъекции, XSS, неавторизованный доступ
- **Конкурентность**: конфликты версий, блокировки
- **Бизнес-правила**: нарушение ограничений целостности

**Запуск негативных тестов:**
```bash
pytest tests/error/ -v
pytest -m error
```

### 4. Тесты производительности (`performance/`)

Измеряют производительность и нагрузочную способность:

- **Создание данных**: время создания множественных записей
- **Запросы**: производительность поиска и фильтрации
- **Конкурентность**: одновременные операции
- **Масштабирование**: работа с большими объемами данных

**Запуск тестов производительности:**
```bash
pytest tests/performance/ -v --tb=short
pytest -m performance
pytest -m slow  # медленные тесты
```

## Маркеры pytest

Система использует следующие маркеры для категоризации тестов:

- `@pytest.mark.unit` - Unit тесты
- `@pytest.mark.integration` - Интеграционные тесты
- `@pytest.mark.error` - Негативные тесты
- `@pytest.mark.performance` - Тесты производительности
- `@pytest.mark.slow` - Медленные тесты (>5 секунд)
- `@pytest.mark.auth` - Тесты авторизации
- `@pytest.mark.database` - Тесты базы данных

## Fixtures

### Основные fixtures (в `conftest.py`)

- **`client`** - Flask test client
- **`auth_headers_admin`** - Заголовки админа для API запросов
- **`auth_headers_engineer`** - Заголовки инженера
- **`auth_headers_user`** - Заголовки обычного пользователя
- **`sample_route`** - Тестовый технологический маршрут
- **`sample_bom_item`** - Тестовый элемент BOM
- **`sample_operation`** - Тестовая операция

### Использование fixtures

```python
def test_create_route(client, auth_headers_admin):
    """Тест создания маршрута"""
    data = {'name': 'Тестовый маршрут'}
    response = client.post('/api/routes', 
                          json=data, 
                          headers=auth_headers_admin)
    assert response.status_code == 201
```

## Запуск тестов

### Все тесты
```bash
pytest
```

### По категориям
```bash
pytest -m unit                    # Только unit тесты
pytest -m integration             # Только интеграционные
pytest -m error                   # Только негативные
pytest -m performance             # Только производительность
```

### По директориям
```bash
pytest tests/unit/               # Unit тесты
pytest tests/integration/        # Интеграционные тесты
pytest tests/error/              # Негативные тесты
pytest tests/performance/        # Тесты производительности
```

### Конкретные файлы
```bash
pytest tests/unit/test_models.py
pytest tests/integration/test_routes_api.py
pytest tests/error/test_bom_errors.py
```

### Параллельный запуск
```bash
pytest -n auto                   # Автоматическое определение CPU
pytest -n 4                      # 4 параллельных процесса
```

### С покрытием кода
```bash
pytest --cov=app --cov-report=html
pytest --cov=app --cov-report=term-missing
```

### Подробный вывод
```bash
pytest -v                        # Verbose mode
pytest -s                        # Показать print()
pytest --tb=short                # Короткий traceback
pytest --tb=long                 # Полный traceback
```

### Фильтрация по имени
```bash
pytest -k "test_create"          # Тесты содержащие "test_create"
pytest -k "route and not error"  # Тесты маршрутов, но не ошибок
```

## Конфигурация среды

### Переменные окружения

Создайте файл `.env.test` для тестовой среды:

```env
# База данных
DATABASE_URL=postgresql://test_user:test_pass@localhost/test_mes_db

# Flask
FLASK_ENV=testing
SECRET_KEY=test-secret-key

# JWT
JWT_SECRET_KEY=test-jwt-secret

# Тестирование
TESTING=True
```

### Настройка базы данных

Для тестов используется отдельная тестовая база данных:

```bash
# Создание тестовой БД
createdb test_mes_db

# Применение миграций
flask db upgrade

# Заполнение тестовыми данными
python -c "from app.seed_data import seed_all; seed_all()"
```

## Отчетность

### HTML отчет о покрытии
```bash
pytest --cov=app --cov-report=html
# Результат в htmlcov/index.html
```

### XML отчет для CI/CD
```bash
pytest --cov=app --cov-report=xml --junitxml=test-results.xml
```

### Отчет производительности
```bash
pytest tests/performance/ --durations=10
```

## Лучшие практики

### 1. Именование тестов

- Используйте описательные имена: `test_create_route_with_valid_data`
- Включайте ожидаемое поведение: `test_create_route_returns_201_status`
- Для негативных тестов: `test_create_route_with_empty_name_returns_400`

### 2. Организация тестов

- Группируйте связанные тесты в классы
- Используйте docstrings для описания назначения
- Следуйте принципу AAA: Arrange, Act, Assert

```python
class TestRouteCreation:
    """Тесты создания технологических маршрутов"""
    
    def test_create_route_with_valid_data(self, client, auth_headers_admin):
        """
        Тест: создание маршрута с корректными данными
        Ожидание: статус 201, корректный response
        """
        # Arrange
        data = {'name': 'Тестовый маршрут'}
        
        # Act
        response = client.post('/api/routes', 
                              json=data, 
                              headers=auth_headers_admin)
        
        # Assert
        assert response.status_code == 201
        assert 'id' in response.json
```

### 3. Изоляция тестов

- Каждый тест должен быть независимым
- Используйте fresh fixtures для каждого теста
- Очищайте данные после тестов (через rollback)

### 4. Управление тестовыми данными

- Создавайте минимально необходимые данные
- Используйте factories для создания объектов
- Не зависьте от конкретных ID или порядка записей

## Отладка тестов

### Пошаговая отладка
```bash
pytest --pdb                     # Запуск debugger при ошибке
pytest --pdb-trace              # Останов в начале каждого теста
```

### Логирование
```bash
pytest -s --log-cli-level=DEBUG # Показать все логи
pytest --log-file=test.log      # Записать логи в файл
```

### Профилирование
```bash
pytest --profile               # Профилирование выполнения
pytest --durations=0          # Время выполнения всех тестов
```

## Интеграция с CI/CD

### GitHub Actions пример

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Мониторинг качества

### Метрики покрытия кода

- **Минимум**: 80% покрытие для новых функций
- **Цель**: 90%+ покрытие критической логики
- **Отслеживание**: регрессия покрытия в PR

### Стандарты производительности

- **API ответы**: < 200ms для простых запросов
- **Создание записей**: < 500ms на запись
- **Пагинация**: < 100ms на страницу
- **Конкурентность**: 80%+ успешных операций

### Обязательные проверки

Перед коммитом все тесты должны проходить:

```bash
# Быстрая проверка
pytest -m "not slow" --maxfail=1

# Полная проверка
pytest --cov=app --cov-fail-under=80

# Проверка стиля кода (если используется)
flake8 app tests
black --check app tests
```

## Поддержка и обновление

### Обновление тестов

- Добавляйте тесты для новой функциональности
- Обновляйте существующие тесты при изменении API
- Удаляйте устаревшие тесты

### Рефакторинг

- Выносите общую логику в fixtures
- Создавайте helper функции для сложных setup'ов
- Документируйте сложные тестовые сценарии

### Мониторинг

- Следите за временем выполнения тестов
- Анализируйте flaky тесты (нестабильные)
- Оптимизируйте медленные тесты 