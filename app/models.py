from app import db, bcrypt
from datetime import datetime, timedelta
from flask import current_app
import secrets
import pyotp
import qrcode
import io
import base64
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import json

# Association table for many-to-many relationship between users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class User(db.Model):
    """User model with authentication and 2FA support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    
    # 2FA fields
    totp_secret = db.Column(db.String(32), nullable=True)
    backup_codes = db.Column(db.Text, nullable=True)  # JSON string of backup codes
    is_2fa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Account security fields
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                           backref=db.backref('users', lazy=True))
    
    def __init__(self, username, email, password, phone_number=None):
        self.username = username
        self.email = email
        self.phone_number = phone_number
        self.set_password(password)
    
    def set_password(self, password):
        """Hash and set the user's password using Argon2"""
        ph = PasswordHasher()
        self.password_hash = ph.hash(password)
    
    def check_password(self, password):
        """Verify the user's password"""
        ph = PasswordHasher()
        try:
            ph.verify(self.password_hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    def is_locked(self):
        """Check if the account is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self):
        """Lock the account for the configured duration"""
        lockout_duration = timedelta(minutes=current_app.config['LOCKOUT_DURATION_MINUTES'])
        self.locked_until = datetime.utcnow() + lockout_duration
        self.failed_login_attempts = current_app.config['MAX_LOGIN_ATTEMPTS']
    
    def unlock_account(self):
        """Unlock the account and reset failed attempts"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and lock if necessary"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= current_app.config['MAX_LOGIN_ATTEMPTS']:
            self.lock_account()
    
    def reset_failed_attempts(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.last_login = datetime.utcnow()
    
    def setup_2fa(self):
        """Generate TOTP secret and backup codes for 2FA setup"""
        # Generate TOTP secret
        self.totp_secret = pyotp.random_base32()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = json.dumps(backup_codes)
        
        return backup_codes
    
    def get_totp_uri(self):
        """Get TOTP URI for QR code generation"""
        if not self.totp_secret:
            return None
        
        totp = pyotp.TOTP(self.totp_secret)
        return totp.provisioning_uri(
            name=self.username,
            issuer_name=current_app.config['APP_NAME']
        )
    
    def get_qr_code(self):
        """Generate QR code for TOTP setup"""
        uri = self.get_totp_uri()
        if not uri:
            return None
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_totp(self, token):
        """Verify TOTP token"""
        if not self.totp_secret:
            return False
        
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if not self.backup_codes:
            return False
        
        backup_codes = json.loads(self.backup_codes)
        code_upper = code.upper()
        
        if code_upper in backup_codes:
            backup_codes.remove(code_upper)
            self.backup_codes = json.dumps(backup_codes)
            return True
        
        return False
    
    def enable_2fa(self):
        """Enable 2FA for the user"""
        self.is_2fa_enabled = True
    
    def disable_2fa(self):
        """Disable 2FA and clear secrets"""
        self.is_2fa_enabled = False
        self.totp_secret = None
        self.backup_codes = None
    
    def has_permission(self, permission_name):
        """Check if user has a specific permission"""
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False
    
    def has_role(self, role_name):
        """Check if user has a specific role"""
        for role in self.roles:
            if role.name == role_name:
                return True
        return False
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'is_2fa_enabled': self.is_2fa_enabled,
            'is_active': self.is_active,
            'is_locked': self.is_locked(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'roles': [role.name for role in self.roles],
            'permissions': list(set([perm.name for role in self.roles for perm in role.permissions]))
        }

class Role(db.Model):
    """Role model for RBAC"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_system_role = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    permissions = db.relationship('Permission', secondary=role_permissions, lazy='subquery',
                                backref=db.backref('roles', lazy=True))
    
    def __init__(self, name, description=None, is_system_role=False):
        self.name = name
        self.description = description
        self.is_system_role = is_system_role
    
    def to_dict(self):
        """Convert role to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_system_role': self.is_system_role,
            'permissions': [perm.name for perm in self.permissions],
            'user_count': len(self.users)
        }

class Permission(db.Model):
    """Permission model for RBAC"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    resource = db.Column(db.String(50), nullable=False)  # e.g., 'tasks', 'routes', 'reports'
    action = db.Column(db.String(20), nullable=False)    # e.g., 'create', 'read', 'update', 'delete'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, name, description, resource, action):
        self.name = name
        self.description = description
        self.resource = resource
        self.action = action
    
    def to_dict(self):
        """Convert permission to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action
        }

class AuditLog(db.Model):
    """Audit log model for tracking authentication and authorization events"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)  # Store username for deleted users
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, nullable=False, index=True)
    event_metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    user = db.relationship('User', backref='audit_logs')
    
    def __init__(self, event_type, event_description, success, user_id=None, 
                 username=None, ip_address=None, user_agent=None, metadata=None):
        self.event_type = event_type
        self.event_description = event_description
        self.success = success
        self.user_id = user_id
        self.username = username
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.event_metadata = json.dumps(metadata) if metadata else None
    
    def to_dict(self):
        """Convert audit log to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'event_type': self.event_type,
            'event_description': self.event_description,
            'ip_address': self.ip_address,
            'success': self.success,
            'metadata': json.loads(self.event_metadata) if self.event_metadata else None,
            'timestamp': self.timestamp.isoformat()
        } 