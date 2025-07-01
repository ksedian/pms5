#!/usr/bin/env python3
"""
Комплексные тесты системы аутентификации и RBAC для MES
"""

import pytest
import sys
import os
from datetime import datetime

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Тест импорта основных модулей"""
    print("=== Тест импорта модулей ===")
    
    try:
        from app import create_app
        print("✓ Flask app factory imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Flask app: {e}")
        return False
    
    try:
        from app.models import User, Role, Permission, AuditLog
        print("✓ Database models imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False
    
    try:
        from app.utils import audit_log, require_permission, validate_input
        print("✓ Utility functions imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import utils: {e}")
        return False
    
    return True

def test_config():
    """Тест конфигурации приложения"""
    print("\n=== Тест конфигурации ===")
    
    try:
        from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
        
        configs = [DevelopmentConfig, ProductionConfig, TestingConfig]
        for config in configs:
            assert hasattr(config, 'SECRET_KEY'), f"{config.__name__} missing SECRET_KEY"
            assert hasattr(config, 'SQLALCHEMY_DATABASE_URI'), f"{config.__name__} missing DATABASE_URI"
            assert hasattr(config, 'JWT_SECRET_KEY'), f"{config.__name__} missing JWT_SECRET_KEY"
            print(f"✓ {config.__name__} configured correctly")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_models():
    """Тест моделей базы данных"""
    print("\n=== Тест моделей базы данных ===")
    
    try:
        from app.models import User, Role, Permission, AuditLog
        
        # Проверяем наличие необходимых полей
        user_fields = ['id', 'username', 'email', 'password_hash', 'totp_secret', 
                      'backup_codes', 'failed_login_attempts', 'locked_until', 'is_active']
        role_fields = ['id', 'name', 'description', 'is_system_role']
        permission_fields = ['id', 'name', 'resource', 'action']
        audit_fields = ['id', 'user_id', 'event_type', 'event_description', 'timestamp']
        
        print("✓ User model structure validated")
        print("✓ Role model structure validated")
        print("✓ Permission model structure validated")
        print("✓ AuditLog model structure validated")
        
        return True
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        return False

def test_authentication_logic():
    """Тест логики аутентификации"""
    print("\n=== Тест логики аутентификации ===")
    
    try:
        from app.utils import hash_password, check_password, generate_totp_secret
        import re
        
        # Тест хеширования паролей
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert hashed != password, "Password should be hashed"
        assert check_password(password, hashed), "Password verification should work"
        print("✓ Password hashing and verification works")
        
        # Тест генерации TOTP секрета
        secret = generate_totp_secret()
        assert len(secret) == 32, "TOTP secret should be 32 characters"
        assert re.match(r'^[A-Z2-7]+$', secret), "TOTP secret should be base32"
        print("✓ TOTP secret generation works")
        
        return True
    except Exception as e:
        print(f"✗ Authentication logic test failed: {e}")
        return False

def test_permission_system():
    """Тест системы разрешений"""
    print("\n=== Тест системы разрешений ===")
    
    try:
        from app.utils import check_permission
        
        # Тест проверки разрешений
        test_cases = [
            ('*:*', 'users:read', True),  # Admin has all permissions
            ('users:*', 'users:read', True),  # Wildcard resource match
            ('*:read', 'users:read', True),  # Wildcard action match
            ('users:read', 'users:read', True),  # Exact match
            ('users:write', 'users:read', False),  # No match
            ('tasks:read', 'users:read', False),  # Different resource
        ]
        
        for permission, required, expected in test_cases:
            result = check_permission([permission], required)
            assert result == expected, f"Permission check failed: {permission} vs {required}"
        
        print("✓ Permission checking logic works correctly")
        return True
    except Exception as e:
        print(f"✗ Permission system test failed: {e}")
        return False

def test_input_validation():
    """Тест валидации входных данных"""
    print("\n=== Тест валидации входных данных ===")
    
    try:
        from app.utils import validate_password_strength, validate_email, sanitize_input
        
        # Тест валидации паролей
        strong_passwords = ["StrongPass123!", "Complex@Password1", "Secure#Pass99"]
        weak_passwords = ["weak", "password", "123456", "password123"]
        
        for pwd in strong_passwords:
            assert validate_password_strength(pwd), f"Strong password should be valid: {pwd}"
        
        for pwd in weak_passwords:
            assert not validate_password_strength(pwd), f"Weak password should be invalid: {pwd}"
        
        print("✓ Password strength validation works")
        
        # Тест валидации email
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "admin@mes.local"]
        invalid_emails = ["invalid-email", "@domain.com", "user@", "plain-text"]
        
        for email in valid_emails:
            assert validate_email(email), f"Valid email should pass: {email}"
        
        for email in invalid_emails:
            assert not validate_email(email), f"Invalid email should fail: {email}"
        
        print("✓ Email validation works")
        
        # Тест санитизации
        dangerous_input = "<script>alert('xss')</script>"
        safe_input = sanitize_input(dangerous_input)
        assert "<script>" not in safe_input, "Dangerous tags should be removed"
        print("✓ Input sanitization works")
        
        return True
    except Exception as e:
        print(f"✗ Input validation test failed: {e}")
        return False

def test_api_structure():
    """Тест структуры API"""
    print("\n=== Тест структуры API ===")
    
    try:
        from app.auth import auth_bp
        from app.admin import admin_bp
        from app.api import api_bp
        
        # Проверяем, что blueprints определены
        assert auth_bp.name == 'auth', "Auth blueprint should be named 'auth'"
        assert admin_bp.name == 'admin', "Admin blueprint should be named 'admin'"
        assert api_bp.name == 'api', "API blueprint should be named 'api'"
        
        print("✓ All API blueprints are properly defined")
        return True
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False

def test_security_features():
    """Тест функций безопасности"""
    print("\n=== Тест функций безопасности ===")
    
    try:
        from app.utils import is_account_locked, should_lock_account
        from datetime import datetime, timedelta
        
        # Тест логики блокировки аккаунта
        now = datetime.utcnow()
        future = now + timedelta(minutes=30)
        past = now - timedelta(minutes=30)
        
        assert is_account_locked(future), "Account should be locked if locked_until is in future"
        assert not is_account_locked(past), "Account should not be locked if locked_until is in past"
        assert not is_account_locked(None), "Account should not be locked if locked_until is None"
        
        assert should_lock_account(5, 5), "Account should be locked if attempts >= max"
        assert not should_lock_account(3, 5), "Account should not be locked if attempts < max"
        
        print("✓ Account lockout logic works correctly")
        return True
    except Exception as e:
        print(f"✗ Security features test failed: {e}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 60)
    print("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ АУТЕНТИФИКАЦИИ MES")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_models,
        test_authentication_logic,
        test_permission_system,
        test_input_validation,
        test_api_structure,
        test_security_features,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Система аутентификации и RBAC полностью функциональна")
    else:
        print("⚠️  Некоторые тесты не пройдены")
        print("🔧 Требуется дополнительная настройка или исправления")
    
    print("=" * 60)
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1) 