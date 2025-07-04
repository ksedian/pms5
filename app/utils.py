from flask import request, current_app
from app import db
from app.models import AuditLog
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import re
import html
import bleach

def log_audit_event(event_type, event_description, success, user_id=None, username=None, metadata=None):
    """
    Log an audit event to the database
    
    Args:
        event_type: Type of event (login, logout, permission_change, etc.)
        event_description: Human readable description of the event
        success: Boolean indicating if the event was successful
        user_id: ID of the user (if applicable)
        username: Username (if user_id not available)
        metadata: Additional data as dictionary
    """
    try:
        # Get request context information
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        # Create audit log entry
        audit_log = AuditLog(
            event_type=event_type,
            event_description=event_description,
            success=success,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
    except Exception as e:
        # Log the error but don't break the application
        current_app.logger.error(f"Failed to log audit event: {str(e)}")
        db.session.rollback()

def require_permission(permission_name):
    """
    Decorator to require specific permission for accessing an endpoint
    
    Usage:
        @require_permission('tasks:read')
        def get_tasks():
            ...
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            from app.models import User
            
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                log_audit_event(
                    'authorization_failure',
                    f'User not found for JWT token: {current_user_id}',
                    False,
                    user_id=current_user_id
                )
                return {'message': 'User not found'}, 401
            
            if not user.is_active:
                log_audit_event(
                    'authorization_failure',
                    f'Inactive user attempted access: {user.username}',
                    False,
                    user_id=user.id,
                    username=user.username
                )
                return {'message': 'Account is inactive'}, 403
            
            if not user.has_permission(permission_name):
                log_audit_event(
                    'authorization_failure',
                    f'User {user.username} attempted access without permission: {permission_name}',
                    False,
                    user_id=user.id,
                    username=user.username,
                    metadata={'required_permission': permission_name}
                )
                return {'message': f'Permission denied: {permission_name}'}, 403
            
            # Permission check passed
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_role(role_name):
    """
    Decorator to require specific role for accessing an endpoint
    
    Usage:
        @require_role('admin')
        def admin_function():
            ...
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            from app.models import User
            
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'message': 'User not found'}, 401
            
            if not user.is_active:
                return {'message': 'Account is inactive'}, 403
            
            if not user.has_role(role_name):
                log_audit_event(
                    'authorization_failure',
                    f'User {user.username} attempted access without role: {role_name}',
                    False,
                    user_id=user.id,
                    username=user.username,
                    metadata={'required_role': role_name}
                )
                return {'message': f'Role required: {role_name}'}, 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_current_user():
    """
    Get the current authenticated user from JWT token
    """
    from app.models import User
    from flask_jwt_extended import get_jwt_identity
    
    try:
        current_user_id = get_jwt_identity()
        if current_user_id:
            return User.query.get(current_user_id)
    except Exception:
        pass
    
    return None

def validate_password_strength(password):
    """
    Validate password strength according to security requirements
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def format_phone_number(phone):
    """
    Format phone number for SMS sending
    
    Args:
        phone: Phone number string
        
    Returns:
        str: Formatted phone number with country code
    """
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Add country code if not present (assuming US)
    if len(digits) == 10:
        digits = '1' + digits
    elif len(digits) == 11 and digits.startswith('1'):
        pass  # Already has country code
    else:
        return None  # Invalid format
    
    return '+' + digits

def generate_backup_codes():
    """
    Generate a set of backup codes for 2FA recovery
    
    Returns:
        list: List of backup codes
    """
    import secrets
    return [secrets.token_hex(4).upper() for _ in range(10)]

def sanitize_input(value):
    """Санитизация входных данных для защиты от XSS"""
    if not value:
        return value
    
    if isinstance(value, str):
        # Удаляем опасные HTML теги и скрипты
        cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)
        # Экранируем HTML символы
        return html.escape(cleaned)
    
    return value

def validate_string_length(value, field_name, max_length=None, min_length=None):
    """Валидация длины строки"""
    if value is None:
        return True
    
    if not isinstance(value, str):
        raise ValueError(f"{field_name} должно быть строкой")
    
    if min_length and len(value) < min_length:
        raise ValueError(f"{field_name} должно содержать минимум {min_length} символов")
    
    if max_length and len(value) > max_length:
        raise ValueError(f"{field_name} не должно превышать {max_length} символов")
    
    return True

def validate_sql_injection(value):
    """Проверка на SQL инъекции"""
    if not value or not isinstance(value, str):
        return True
    
    # Список опасных SQL ключевых слов
    dangerous_patterns = [
        r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
        r'[;\'"\\]',  # Опасные символы
        r'--',        # SQL комментарии
        r'/\*.*?\*/', # Блочные комментарии
        r'\bor\s+1\s*=\s*1\b',  # Классические OR инъекции
        r'\band\s+1\s*=\s*1\b', # Классические AND инъекции
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value.lower(), re.IGNORECASE):
            raise ValueError("Обнаружена попытка SQL инъекции")
    
    return True

def validate_route_data(data):
    """Комплексная валидация данных технологического маршрута"""
    if not data:
        raise ValueError("Данные маршрута не могут быть пустыми")
    
    # Валидация обязательных полей
    if not data.get('name'):
        raise ValueError("Название маршрута обязательно")
    
    if not data.get('route_number'):
        raise ValueError("Номер маршрута обязателен")
    
    # Валидация длины полей
    validate_string_length(data.get('name'), 'Название', max_length=200, min_length=2)
    validate_string_length(data.get('route_number'), 'Номер маршрута', max_length=50, min_length=1)
    validate_string_length(data.get('description'), 'Описание', max_length=5000)
    
    # Проверка на SQL инъекции
    validate_sql_injection(data.get('name'))
    validate_sql_injection(data.get('route_number'))
    validate_sql_injection(data.get('description'))
    
    # Санитизация
    data['name'] = sanitize_input(data['name'])
    data['route_number'] = sanitize_input(data['route_number'])
    if data.get('description'):
        data['description'] = sanitize_input(data['description'])
    
    # Валидация status
    valid_statuses = ['draft', 'active', 'archived']
    if data.get('status') and data['status'] not in valid_statuses:
        raise ValueError(f"Недопустимый статус. Разрешенные: {valid_statuses}")
    
    # Валидация complexity_level
    valid_complexity = ['low', 'medium', 'high']
    if data.get('complexity_level') and data['complexity_level'] not in valid_complexity:
        raise ValueError(f"Недопустимый уровень сложности. Разрешенные: {valid_complexity}")
    
    # Валидация estimated_duration
    if data.get('estimated_duration') is not None:
        try:
            duration = float(data['estimated_duration'])
            if duration < 0:
                raise ValueError("Продолжительность не может быть отрицательной")
        except (ValueError, TypeError):
            raise ValueError("Продолжительность должна быть числом")
    
    return data

def validate_bom_data(data):
    """Комплексная валидация данных BOM"""
    if not data:
        raise ValueError("Данные BOM не могут быть пустыми")
    
    # Валидация обязательных полей
    if not data.get('part_number'):
        raise ValueError("Номер детали обязателен")
    
    if not data.get('name'):
        raise ValueError("Название детали обязательно")
    
    # Валидация длины полей
    validate_string_length(data.get('part_number'), 'Номер детали', max_length=100, min_length=1)
    validate_string_length(data.get('name'), 'Название', max_length=200, min_length=2)
    validate_string_length(data.get('description'), 'Описание', max_length=5000)
    validate_string_length(data.get('unit'), 'Единица измерения', max_length=20)
    validate_string_length(data.get('material_type'), 'Тип материала', max_length=50)
    
    # Проверка на SQL инъекции
    validate_sql_injection(data.get('part_number'))
    validate_sql_injection(data.get('name'))
    validate_sql_injection(data.get('description'))
    validate_sql_injection(data.get('unit'))
    validate_sql_injection(data.get('material_type'))
    
    # Санитизация
    data['part_number'] = sanitize_input(data['part_number'])
    data['name'] = sanitize_input(data['name'])
    if data.get('description'):
        data['description'] = sanitize_input(data['description'])
    if data.get('unit'):
        data['unit'] = sanitize_input(data['unit'])
    if data.get('material_type'):
        data['material_type'] = sanitize_input(data['material_type'])
    
    # Валидация quantity
    if data.get('quantity') is not None:
        try:
            quantity = float(data['quantity'])
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным числом")
        except (ValueError, TypeError):
            raise ValueError("Количество должно быть числом")
    
    # Валидация cost_per_unit
    if data.get('cost_per_unit') is not None:
        try:
            cost = float(data['cost_per_unit'])
            if cost < 0:
                raise ValueError("Стоимость не может быть отрицательной")
        except (ValueError, TypeError):
            raise ValueError("Стоимость должна быть числом")
    
    # Валидация currency
    valid_currencies = ['RUB', 'USD', 'EUR']
    if data.get('currency') and data['currency'] not in valid_currencies:
        raise ValueError(f"Недопустимая валюта. Разрешенные: {valid_currencies}")
    
    return data

def is_safe_url(target):
    """
    Check if a redirect URL is safe (prevents open redirect attacks)
    
    Args:
        target: URL to check
        
    Returns:
        bool: True if URL is safe for redirect
    """
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc 

def validate_operation_data(data):
    """Комплексная валидация данных операций"""
    if not data:
        raise ValueError("Данные операции не могут быть пустыми")
    
    # Валидация обязательных полей
    if not data.get('name'):
        raise ValueError("Название операции обязательно")
    
    if not data.get('operation_code'):
        raise ValueError("Код операции обязателен")
    
    if not data.get('operation_type'):
        raise ValueError("Тип операции обязателен")
    
    # Валидация длины полей
    validate_string_length(data.get('name'), 'Название', max_length=200, min_length=2)
    validate_string_length(data.get('operation_code'), 'Код операции', max_length=50, min_length=1)
    validate_string_length(data.get('operation_type'), 'Тип операции', max_length=50, min_length=1)
    validate_string_length(data.get('description'), 'Описание', max_length=5000)
    
    # Проверка на SQL инъекции
    validate_sql_injection(data.get('name'))
    validate_sql_injection(data.get('operation_code'))
    validate_sql_injection(data.get('operation_type'))
    validate_sql_injection(data.get('description'))
    
    # Санитизация
    data['name'] = sanitize_input(data['name'])
    data['operation_code'] = sanitize_input(data['operation_code'])
    data['operation_type'] = sanitize_input(data['operation_type'])
    if data.get('description'):
        data['description'] = sanitize_input(data['description'])
    
    # Валидация типов операций
    valid_operation_types = ['machining', 'assembly', 'inspection', 'testing', 'packaging']
    if data.get('operation_type') and data['operation_type'] not in valid_operation_types:
        raise ValueError(f"Недопустимый тип операции. Разрешенные: {valid_operation_types}")
    
    # Валидация времени
    if data.get('setup_time') is not None:
        try:
            setup_time = float(data['setup_time'])
            if setup_time < 0:
                raise ValueError("Время настройки не может быть отрицательным")
        except (ValueError, TypeError):
            raise ValueError("Время настройки должно быть числом")
    
    if data.get('operation_time') is not None:
        try:
            operation_time = float(data['operation_time'])
            if operation_time < 0:
                raise ValueError("Время операции не может быть отрицательным")
        except (ValueError, TypeError):
            raise ValueError("Время операции должно быть числом")
    
    return data 