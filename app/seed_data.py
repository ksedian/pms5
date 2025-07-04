from app import db
from app.models import Role, Permission, User

def create_default_permissions():
    """Create default permissions for the MES system"""
    permissions_data = [
        # Task permissions
        ('tasks:create', 'Create new tasks', 'tasks', 'create'),
        ('tasks:read', 'View tasks', 'tasks', 'read'),
        ('tasks:update', 'Update tasks', 'tasks', 'update'),
        ('tasks:delete', 'Delete tasks', 'tasks', 'delete'),
        
        # Route permissions (extended for technological routes)
        ('routes:create', 'Create new routes', 'routes', 'create'),
        ('routes:read', 'View routes', 'routes', 'read'),
        ('routes:update', 'Update routes', 'routes', 'update'),
        ('routes:delete', 'Delete routes', 'routes', 'delete'),
        
        # Operation permissions
        ('operations:create', 'Create new operations', 'operations', 'create'),
        ('operations:read', 'View operations', 'operations', 'read'),
        ('operations:update', 'Update operations', 'operations', 'update'),
        ('operations:delete', 'Delete operations', 'operations', 'delete'),
        
        # BOM permissions
        ('bom:create', 'Create new BOM items', 'bom', 'create'),
        ('bom:read', 'View BOM items', 'bom', 'read'),
        ('bom:update', 'Update BOM items', 'bom', 'update'),
        ('bom:delete', 'Delete BOM items', 'bom', 'delete'),
        
        # Report permissions
        ('reports:create', 'Create new reports', 'reports', 'create'),
        ('reports:read', 'View reports', 'reports', 'read'),
        ('reports:update', 'Update reports', 'reports', 'update'),
        ('reports:delete', 'Delete reports', 'reports', 'delete'),
        
        # User management permissions
        ('users:create', 'Create new users', 'users', 'create'),
        ('users:read', 'View users', 'users', 'read'),
        ('users:update', 'Update users', 'users', 'update'),
        ('users:delete', 'Delete users', 'users', 'delete'),
        
        # Role management permissions
        ('roles:create', 'Create new roles', 'roles', 'create'),
        ('roles:read', 'View roles', 'roles', 'read'),
        ('roles:update', 'Update roles', 'roles', 'update'),
        ('roles:delete', 'Delete roles', 'roles', 'delete'),
        
        # System permissions
        ('system:admin', 'System administration', 'system', 'admin'),
        ('audit_logs:read', 'View audit logs', 'audit_logs', 'read'),
    ]
    
    for name, description, resource, action in permissions_data:
        if not Permission.query.filter_by(name=name).first():
            permission = Permission(name, description, resource, action)
            db.session.add(permission)
    
    db.session.commit()
    print("Default permissions created successfully")

def create_default_roles():
    """Create default roles for the MES system"""
    # Create permissions first
    create_default_permissions()
    
    roles_data = [
        ('worker', 'Basic worker role with limited access', [
            'tasks:read', 'tasks:update', 'routes:read'
        ]),
        ('engineer', 'Engineer role with extended access', [
            'tasks:create', 'tasks:read', 'tasks:update', 'tasks:delete',
            'routes:create', 'routes:read', 'routes:update', 'routes:delete',
            'operations:create', 'operations:read', 'operations:update', 'operations:delete',
            'bom:create', 'bom:read', 'bom:update', 'bom:delete',
            'reports:read'
        ]),
        ('manager', 'Manager role with management access', [
            'tasks:create', 'tasks:read', 'tasks:update', 'tasks:delete',
            'routes:create', 'routes:read', 'routes:update', 'routes:delete',
            'reports:create', 'reports:read', 'reports:update', 'reports:delete',
            'users:read', 'audit_logs:read'
        ]),
        ('admin', 'Administrator role with full access', [
            'tasks:create', 'tasks:read', 'tasks:update', 'tasks:delete',
            'routes:create', 'routes:read', 'routes:update', 'routes:delete',
            'operations:create', 'operations:read', 'operations:update', 'operations:delete',
            'bom:create', 'bom:read', 'bom:update', 'bom:delete',
            'reports:create', 'reports:read', 'reports:update', 'reports:delete',
            'users:create', 'users:read', 'users:update', 'users:delete',
            'roles:create', 'roles:read', 'roles:update', 'roles:delete',
            'system:admin', 'audit_logs:read'
        ])
    ]
    
    for role_name, description, permission_names in roles_data:
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(role_name, description, is_system_role=True)
            db.session.add(role)
            db.session.flush()  # Flush to get the role ID
        
        # Clear existing permissions
        role.permissions.clear()
        
        # Add permissions to role
        for permission_name in permission_names:
            permission = Permission.query.filter_by(name=permission_name).first()
            if permission:
                role.permissions.append(permission)
    
    db.session.commit()
    print("Default roles created successfully")

def create_admin_user():
    """Create default admin user"""
    admin_username = 'admin'
    admin_email = 'admin@mes.local'
    admin_password = 'admin123'
    
    # Check if admin user already exists
    admin_user = User.query.filter_by(username=admin_username).first()
    if admin_user:
        print("Admin user already exists")
        return
    
    # Create admin user
    admin_user = User(
        username=admin_username,
        email=admin_email,
        password=admin_password
    )
    
    # Assign admin role
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role:
        admin_user.roles.append(admin_role)
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"Admin user created: {admin_username} / {admin_password}")

def seed_all():
    """Seed all default data"""
    print("Seeding database with default data...")
    create_default_roles()
    create_admin_user()
    print("Database seeding completed") 