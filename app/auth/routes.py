from app.auth import bp
from app import db
from app.models import User, Role
from app.utils import log_audit_event, get_current_user
from flask import request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import re

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user account"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password']
        
        # Basic validation
        if len(username) < 3 or len(username) > 80:
            return jsonify({'message': 'Username must be between 3 and 80 characters'}), 400
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return jsonify({'message': 'Username can only contain letters, numbers, underscores, and hyphens'}), 400
        
        if len(password) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'message': 'Username already exists'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email already exists'}), 409
        
        # Create new user
        user = User(username=username, email=email, password=password)
        
        # Assign default worker role if it exists
        worker_role = Role.query.filter_by(name='worker').first()
        if worker_role:
            user.roles.append(worker_role)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed'}), 500

@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user with username/password"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({'message': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Check if account is locked
        if user.is_locked():
            return jsonify({
                'message': 'Account is locked due to too many failed attempts'
            }), 423
        
        # Check if account is active
        if not user.is_active:
            return jsonify({'message': 'Account is inactive'}), 403
        
        # Verify password
        if not user.check_password(password):
            user.increment_failed_attempts()
            db.session.commit()
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Reset failed attempts on successful login
        user.reset_failed_attempts()
        
        # Log successful login
        log_audit_event(
            'login_success',
            f'User {user.username} logged in successfully',
            True,
            user_id=user.id,
            username=user.username
        )
        
        # Check if 2FA is enabled
        if user.is_2fa_enabled:
            db.session.commit()
            return jsonify({
                'message': 'Password verified. 2FA required.',
                'requires_2fa': True,
                'user_id': user.id
            }), 200
        
        # Generate JWT token for direct login (no 2FA)
        access_token = create_access_token(identity=user.id)
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed'}), 500

@bp.route('/setup-2fa', methods=['POST'])
@jwt_required()
def setup_2fa():
    """Setup 2FA for the current user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.is_2fa_enabled:
            return jsonify({'message': '2FA is already enabled'}), 409
        
        # Setup 2FA and generate backup codes
        backup_codes = user.setup_2fa()
        db.session.commit()
        
        # Log 2FA setup
        log_audit_event(
            '2fa_setup',
            f'User {user.username} started 2FA setup',
            True,
            user_id=user.id,
            username=user.username
        )
        
        return jsonify({
            'message': '2FA setup initiated',
            'totp_uri': user.get_totp_uri(),
            'qr_code': user.get_qr_code(),
            'backup_codes': backup_codes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to setup 2FA'}), 500

@bp.route('/enable-2fa', methods=['POST'])
@jwt_required()
def enable_2fa():
    """Enable 2FA after verifying TOTP code"""
    try:
        data = request.get_json()
        
        if not data or 'totp_code' not in data:
            return jsonify({'message': 'TOTP code is required'}), 400
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if user.is_2fa_enabled:
            return jsonify({'message': '2FA is already enabled'}), 409
        
        # Verify TOTP code
        if not user.verify_totp(data['totp_code']):
            log_audit_event(
                '2fa_enable_failed',
                f'User {user.username} failed to enable 2FA - invalid TOTP code',
                False,
                user_id=user.id,
                username=user.username
            )
            return jsonify({'message': 'Invalid TOTP code'}), 400
        
        # Enable 2FA
        user.enable_2fa()
        db.session.commit()
        
        # Log successful 2FA enablement
        log_audit_event(
            '2fa_enabled',
            f'User {user.username} successfully enabled 2FA',
            True,
            user_id=user.id,
            username=user.username
        )
        
        return jsonify({'message': '2FA enabled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to enable 2FA'}), 500

@bp.route('/disable-2fa', methods=['POST'])
@jwt_required()
def disable_2fa():
    """Disable 2FA for the current user"""
    try:
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({'message': 'Password is required to disable 2FA'}), 400
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if not user.is_2fa_enabled:
            return jsonify({'message': '2FA is not enabled'}), 409
        
        # Verify password
        if not user.check_password(data['password']):
            log_audit_event(
                '2fa_disable_failed',
                f'User {user.username} failed to disable 2FA - incorrect password',
                False,
                user_id=user.id,
                username=user.username
            )
            return jsonify({'message': 'Incorrect password'}), 401
        
        # Disable 2FA
        user.disable_2fa()
        db.session.commit()
        
        # Log 2FA disabling
        log_audit_event(
            '2fa_disabled',
            f'User {user.username} disabled 2FA',
            True,
            user_id=user.id,
            username=user.username
        )
        
        return jsonify({'message': '2FA disabled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to disable 2FA'}), 500

@bp.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    """Verify 2FA code and complete login"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('user_id', 'code')):
            return jsonify({'message': 'User ID and 2FA code are required'}), 400
        
        user_id = data['user_id']
        code = data['code']
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if not user.is_2fa_enabled:
            return jsonify({'message': '2FA is not enabled for this user'}), 400
        
        # Check if account is locked or inactive
        if user.is_locked():
            return jsonify({'message': 'Account is locked'}), 423
        
        if not user.is_active:
            return jsonify({'message': 'Account is inactive'}), 403
        
        # Try TOTP verification first
        verified = user.verify_totp(code)
        verification_method = 'totp'
        
        # If TOTP fails, try backup code
        if not verified:
            verified = user.verify_backup_code(code)
            verification_method = 'backup_code'
        
        if not verified:
            # Increment failed attempts for 2FA failures
            user.increment_failed_attempts()
            db.session.commit()
            
            log_audit_event(
                '2fa_verification_failed',
                f'User {user.username} failed 2FA verification',
                False,
                user_id=user.id,
                username=user.username,
                metadata={'verification_method': 'both'}
            )
            return jsonify({'message': 'Invalid 2FA code'}), 401
        
        # Reset failed attempts on successful 2FA
        user.reset_failed_attempts()
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        db.session.commit()
        
        # Log successful 2FA verification
        log_audit_event(
            '2fa_verification_success',
            f'User {user.username} successfully verified 2FA',
            True,
            user_id=user.id,
            username=user.username,
            metadata={'verification_method': verification_method}
        )
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict(),
            'verification_method': verification_method
        }), 200
        
    except Exception as e:
        return jsonify({'message': '2FA verification failed'}), 500

@bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Refresh JWT token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'message': 'User not found or inactive'}), 401
        
        # Generate new token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Token refresh failed'}), 500

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user:
            log_audit_event(
                'logout',
                f'User {user.username} logged out',
                True,
                user_id=user.id,
                username=user.username
            )
        
        # В реальном приложении здесь бы был blacklist JWT токена
        # Но для простоты просто возвращаем успешный ответ
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Logout failed'}), 500

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch profile'}), 500

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('current_password', 'new_password')):
            return jsonify({'message': 'Current password and new password are required'}), 400
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Verify current password
        if not user.check_password(data['current_password']):
            log_audit_event(
                'password_change_failed',
                f'User {user.username} failed to change password - incorrect current password',
                False,
                user_id=user.id,
                username=user.username
            )
            return jsonify({'message': 'Current password is incorrect'}), 401
        
        # Validate new password strength
        new_password = data['new_password']
        if len(new_password) < 8:
            return jsonify({'message': 'New password must be at least 8 characters long'}), 400
        
        # Set new password
        user.set_password(new_password)
        db.session.commit()
        
        # Log successful password change
        log_audit_event(
            'password_changed',
            f'User {user.username} successfully changed password',
            True,
            user_id=user.id,
            username=user.username
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to change password'}), 500