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

# Association table for many-to-many relationship between technological routes and operations
route_operations = db.Table('route_operations',
    db.Column('route_id', db.Integer, db.ForeignKey('technological_routes.id'), primary_key=True),
    db.Column('operation_id', db.Integer, db.ForeignKey('operations.id'), primary_key=True),
    db.Column('sequence_number', db.Integer, nullable=False),  # Порядок операции в маршруте
    db.Column('is_parallel', db.Boolean, default=False, nullable=False)  # Параллельная операция
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

class TechnologicalRoute(db.Model):
    """Модель технологических маршрутов"""
    __tablename__ = 'technological_routes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    route_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Статус маршрута
    status = db.Column(db.String(20), default='draft', nullable=False)  # draft, active, archived
    
    # Данные графа маршрута (JSON)
    route_data = db.Column(db.Text, nullable=True)  # JSON структура для React Flow
    
    # Версионирование и аудит
    version = db.Column(db.Integer, default=1, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Метаданные
    estimated_duration = db.Column(db.Float, nullable=True)  # Общая продолжительность в часах
    complexity_level = db.Column(db.String(20), default='medium', nullable=False)  # low, medium, high
    
    # Relationships
    creator = db.relationship('User', backref='created_routes')
    operations = db.relationship('Operation', secondary=route_operations, lazy='subquery',
                               backref=db.backref('routes', lazy=True))
    versions = db.relationship('RouteVersion', backref='route', cascade='all, delete-orphan')
    
    def __init__(self, name, route_number, created_by, description=None):
        self.name = name
        self.route_number = route_number
        self.created_by = created_by
        self.description = description
    
    def create_version(self, description=None, user_id=None):
        """Создать новую версию маршрута"""
        version_data = {
            'name': self.name,
            'description': self.description,
            'route_data': self.route_data,
            'operations': [{'id': op.id, 'name': op.name} for op in self.operations]
        }
        
        new_version = RouteVersion(
            route_id=self.id,
            version_number=self.version,
            description=description or f'Версия {self.version}',
            route_data=json.dumps(version_data),
            created_by=user_id or self.created_by
        )
        
        db.session.add(new_version)
        self.version += 1
        return new_version
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'route_number': self.route_number,
            'status': self.status,
            'route_data': json.loads(self.route_data) if self.route_data else None,
            'version': self.version,
            'estimated_duration': self.estimated_duration,
            'complexity_level': self.complexity_level,
            'created_by': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'operations': [op.to_dict() for op in self.operations]
        }

class Operation(db.Model):
    """Модель операций технологического процесса"""
    __tablename__ = 'operations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    operation_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Тип операции
    operation_type = db.Column(db.String(50), nullable=False)  # machining, assembly, inspection, etc.
    
    # Временные характеристики
    setup_time = db.Column(db.Float, default=0.0, nullable=False)  # Время настройки в минутах
    operation_time = db.Column(db.Float, default=0.0, nullable=False)  # Время выполнения в минутах
    
    # Ресурсы
    required_equipment = db.Column(db.Text, nullable=True)  # JSON список оборудования
    required_skills = db.Column(db.Text, nullable=True)  # JSON список навыков
    
    # Параметры качества
    quality_requirements = db.Column(db.Text, nullable=True)  # JSON требования к качеству
    
    # Аудит
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_operations')
    
    def __init__(self, name, operation_code, operation_type, created_by, description=None):
        self.name = name
        self.operation_code = operation_code
        self.operation_type = operation_type
        self.created_by = created_by
        self.description = description
    
    def get_total_time(self):
        """Получить общее время операции"""
        return self.setup_time + self.operation_time
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'operation_code': self.operation_code,
            'operation_type': self.operation_type,
            'setup_time': self.setup_time,
            'operation_time': self.operation_time,
            'total_time': self.get_total_time(),
            'required_equipment': json.loads(self.required_equipment) if self.required_equipment else [],
            'required_skills': json.loads(self.required_skills) if self.required_skills else [],
            'quality_requirements': json.loads(self.quality_requirements) if self.quality_requirements else {},
            'created_by': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class BOMItem(db.Model):
    """Модель элементов спецификации материалов (BOM) с поддержкой иерархии"""
    __tablename__ = 'bom_items'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('bom_items.id'), nullable=True)
    
    # Основная информация
    part_number = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Характеристики
    quantity = db.Column(db.Float, default=1.0, nullable=False)
    unit = db.Column(db.String(20), default='шт', nullable=False)
    material_type = db.Column(db.String(50), nullable=True)
    
    # Стоимость
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=True)
    currency = db.Column(db.String(3), default='RUB', nullable=False)
    
    # Иерархия
    level = db.Column(db.Integer, default=0, nullable=False)  # Автовычисляемый уровень вложенности
    is_assembly = db.Column(db.Boolean, default=False, nullable=False)  # Сборочная единица
    
    # Версионирование
    version = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)  # draft, active, archived
    
    # Технологические данные
    technological_route_id = db.Column(db.Integer, db.ForeignKey('technological_routes.id'), nullable=True)
    
    # Аудит
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships - самосвязь для иерархии
    children = db.relationship('BOMItem', backref=db.backref('parent', remote_side=[id]))
    creator = db.relationship('User', backref='created_bom_items')
    technological_route = db.relationship('TechnologicalRoute', backref='bom_items')
    versions = db.relationship('BOMVersion', backref='bom_item', cascade='all, delete-orphan')
    
    def __init__(self, part_number, name, created_by, parent_id=None, quantity=1.0, unit='шт'):
        self.part_number = part_number
        self.name = name
        self.created_by = created_by
        self.parent_id = parent_id
        self.quantity = quantity
        self.unit = unit
        self._calculate_level()
    
    def _calculate_level(self):
        """Автоматически вычислить уровень вложенности"""
        if self.parent_id is None:
            self.level = 0
        else:
            parent = BOMItem.query.get(self.parent_id)
            self.level = parent.level + 1 if parent else 0
    
    def get_total_cost(self):
        """Вычислить общую стоимость с учетом дочерних элементов"""
        total = float(self.cost_per_unit or 0) * float(self.quantity)
        
        for child in self.children:
            total += child.get_total_cost()
        
        return total
    
    def get_tree_structure(self):
        """Получить полную структуру дерева от текущего узла"""
        result = self.to_dict()
        result['children'] = [child.get_tree_structure() for child in self.children]
        return result
    
    def create_version(self, description=None, user_id=None):
        """Создать новую версию BOM элемента"""
        version_data = {
            'part_number': self.part_number,
            'name': self.name,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'cost_per_unit': float(self.cost_per_unit) if self.cost_per_unit else None,
            'children': [child.to_dict() for child in self.children]
        }
        
        new_version = BOMVersion(
            bom_item_id=self.id,
            version_number=self.version,
            description=description or f'Версия {self.version}',
            bom_data=json.dumps(version_data, ensure_ascii=False),
            created_by=user_id or self.created_by
        )
        
        db.session.add(new_version)
        self.version += 1
        return new_version
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'part_number': self.part_number,
            'name': self.name,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'material_type': self.material_type,
            'cost_per_unit': float(self.cost_per_unit) if self.cost_per_unit else None,
            'currency': self.currency,
            'level': self.level,
            'is_assembly': self.is_assembly,
            'version': self.version,
            'status': self.status,
            'technological_route_id': self.technological_route_id,
            'total_cost': float(self.get_total_cost()),
            'created_by': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_children': len(self.children) > 0
        }

class RouteVersion(db.Model):
    """Модель версий технологических маршрутов"""
    __tablename__ = 'route_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('technological_routes.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Снапшот данных маршрута в JSON
    route_data = db.Column(db.Text, nullable=False)
    
    # Аудит
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_route_versions')
    
    def __init__(self, route_id, version_number, route_data, created_by, description=None):
        self.route_id = route_id
        self.version_number = version_number
        self.route_data = route_data
        self.created_by = created_by
        self.description = description
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'route_id': self.route_id,
            'version_number': self.version_number,
            'description': self.description,
            'route_data': json.loads(self.route_data),
            'created_by': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat()
        }

class BOMVersion(db.Model):
    """Модель версий BOM элементов"""
    __tablename__ = 'bom_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    bom_item_id = db.Column(db.Integer, db.ForeignKey('bom_items.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Снапшот данных BOM в JSON
    bom_data = db.Column(db.Text, nullable=False)
    
    # Аудит
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_bom_versions')
    
    def __init__(self, bom_item_id, version_number, bom_data, created_by, description=None):
        self.bom_item_id = bom_item_id
        self.version_number = version_number
        self.bom_data = bom_data
        self.created_by = created_by
        self.description = description
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'bom_item_id': self.bom_item_id,
            'version_number': self.version_number,
            'description': self.description,
            'bom_data': json.loads(self.bom_data),
            'created_by': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat()
        }

class Archive(db.Model):
    """Модель архивных записей для удаленных данных"""
    __tablename__ = 'archives'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)  # 'route', 'bom_item', 'operation'
    entity_id = db.Column(db.Integer, nullable=False)
    entity_data = db.Column(db.Text, nullable=False)  # JSON с полными данными
    
    # Причина архивирования
    reason = db.Column(db.String(50), default='deleted', nullable=False)  # deleted, replaced, obsolete
    notes = db.Column(db.Text, nullable=True)
    
    # Аудит
    archived_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Связанные архивные записи
    related_archives = db.Column(db.Text, nullable=True)  # JSON список связанных архивов
    
    # Relationships
    archiver = db.relationship('User', backref='archived_items')
    
    def __init__(self, entity_type, entity_id, entity_data, archived_by, reason='deleted', notes=None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.entity_data = entity_data
        self.archived_by = archived_by
        self.reason = reason
        self.notes = notes
    
    def to_dict(self):
        """Преобразовать в словарь для API"""
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'entity_data': json.loads(self.entity_data),
            'reason': self.reason,
            'notes': self.notes,
            'archived_by': self.archiver.username if self.archiver else None,
            'archived_at': self.archived_at.isoformat(),
            'related_archives': json.loads(self.related_archives) if self.related_archives else []
        } 