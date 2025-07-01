from flask import request, current_app
from app import db
from app.models import AuditLog
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

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

def sanitize_input(value, max_length=None, allowed_chars=None):
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        value: Input value to sanitize
        max_length: Maximum allowed length
        allowed_chars: Set of allowed characters (if specified)
        
    Returns:
        str: Sanitized value
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Remove null bytes and control characters
    value = ''.join(char for char in value if ord(char) >= 32)
    
    # Trim to max length
    if max_length:
        value = value[:max_length]
    
    # Filter allowed characters
    if allowed_chars:
        value = ''.join(char for char in value if char in allowed_chars)
    
    # Strip whitespace
    value = value.strip()
    
    return value

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