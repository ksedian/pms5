from app.admin import bp
from app import db
from app.models import User, Role, Permission, AuditLog
from app.utils import require_role, require_permission, log_audit_event, get_current_user
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime

def _get_authenticated_user():
    """Helper function to get current user with authentication check"""
    current_user = get_current_user()
    if not current_user:
        return None, jsonify({'message': 'Authentication required'}), 401
    return current_user, None, None

# ====================
# USER MANAGEMENT
# ====================

@bp.route('/users', methods=['GET'])
@require_role('admin')
def list_users():
    """List all users (admin only)"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
        
        users = User.query.all()
        
        # Log successful admin access
        log_audit_event(
            'admin_access',
            f'Admin {current_user.username} accessed user list',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'list_users', 'user_count': len(users)}
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch users'}), 500

@bp.route('/users/<int:user_id>', methods=['GET'])
@require_role('admin')
def get_user(user_id):
    """Get specific user details"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        user = User.query.get_or_404(user_id)
        
        log_audit_event(
            'admin_access',
            f'Admin {current_user.username} accessed user details for {user.username}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'get_user', 'target_user_id': user_id}
        )
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user'}), 500

@bp.route('/users/<int:user_id>/activate', methods=['POST'])
@require_role('admin')
def activate_user(user_id):
    """Activate user account"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        user = User.query.get_or_404(user_id)
        
        user.is_active = True
        user.unlock_account()  # Also unlock if locked
        db.session.commit()
        
        log_audit_event(
            'user_activation',
            f'Admin {current_user.username} activated user {user.username}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'activate_user', 'target_user_id': user_id, 'target_username': user.username}
        )
        
        return jsonify({'message': 'User activated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to activate user'}), 500

@bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@require_role('admin')
def deactivate_user(user_id):
    """Deactivate user account"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        user = User.query.get_or_404(user_id)
        
        # Prevent self-deactivation
        if user.id == current_user.id:
            return jsonify({'message': 'Cannot deactivate your own account'}), 400
        
        user.is_active = False
        db.session.commit()
        
        log_audit_event(
            'user_deactivation',
            f'Admin {current_user.username} deactivated user {user.username}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'deactivate_user', 'target_user_id': user_id, 'target_username': user.username}
        )
        
        return jsonify({'message': 'User deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to deactivate user'}), 500

@bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@require_role('admin')
def unlock_user(user_id):
    """Unlock user account"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        user = User.query.get_or_404(user_id)
        
        user.unlock_account()
        db.session.commit()
        
        log_audit_event(
            'account_unlock',
            f'Admin {current_user.username} unlocked user {user.username}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'unlock_user', 'target_user_id': user_id, 'target_username': user.username}
        )
        
        return jsonify({'message': 'User unlocked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to unlock user'}), 500

# ====================
# ROLE MANAGEMENT  
# ====================

@bp.route('/roles', methods=['GET'])
@require_permission('roles:read')
def list_roles():
    """List all roles"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        roles = Role.query.all()
        
        log_audit_event(
            'admin_access',
            f'User {current_user.username} accessed roles list',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'list_roles', 'role_count': len(roles)}
        )
        
        return jsonify({
            'roles': [role.to_dict() for role in roles],
            'total': len(roles)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch roles'}), 500

@bp.route('/roles', methods=['POST'])
@require_permission('roles:create')
def create_role():
    """Create new role"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'message': 'Role name is required'}), 400
        
        name = data['name'].strip()
        description = data.get('description', '').strip()
        
        # Check if role already exists
        if Role.query.filter_by(name=name).first():
            return jsonify({'message': 'Role already exists'}), 409
        
        # Create new role
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.commit()
        
        log_audit_event(
            'role_creation',
            f'Admin {current_user.username} created role {name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'create_role', 'role_name': name, 'role_id': role.id}
        )
        
        return jsonify({
            'message': 'Role created successfully',
            'role': role.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create role'}), 500

@bp.route('/roles/<int:role_id>', methods=['PUT'])
@require_permission('roles:update')
def update_role(role_id):
    """Update role"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        role = Role.query.get_or_404(role_id)
        data = request.get_json()
        
        # Prevent modification of system roles
        if role.is_system_role:
            return jsonify({'message': 'Cannot modify system roles'}), 403
        
        old_name = role.name
        
        if 'name' in data:
            role.name = data['name'].strip()
        if 'description' in data:
            role.description = data['description'].strip()
        
        role.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit_event(
            'role_update',
            f'Admin {current_user.username} updated role {old_name} to {role.name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'update_role', 'role_id': role_id, 'old_name': old_name, 'new_name': role.name}
        )
        
        return jsonify({
            'message': 'Role updated successfully',
            'role': role.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update role'}), 500

@bp.route('/roles/<int:role_id>', methods=['DELETE'])
@require_permission('roles:delete')
def delete_role(role_id):
    """Delete role"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        role = Role.query.get_or_404(role_id)
        
        # Prevent deletion of system roles
        if role.is_system_role:
            return jsonify({'message': 'Cannot delete system roles'}), 403
        
        # Check if role is assigned to any users
        if role.users:
            return jsonify({
                'message': f'Cannot delete role. It is assigned to {len(role.users)} users.'
            }), 400
        
        role_name = role.name
        db.session.delete(role)
        db.session.commit()
        
        log_audit_event(
            'role_deletion',
            f'Admin {current_user.username} deleted role {role_name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'delete_role', 'role_id': role_id, 'role_name': role_name}
        )
        
        return jsonify({'message': 'Role deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete role'}), 500

# ====================
# PERMISSION MANAGEMENT
# ====================

@bp.route('/permissions', methods=['GET'])
@require_permission('permissions:read')
def list_permissions():
    """List all permissions"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        permissions = Permission.query.all()
        
        log_audit_event(
            'admin_access',
            f'User {current_user.username} accessed permissions list',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'list_permissions', 'permission_count': len(permissions)}
        )
        
        return jsonify({
            'permissions': [permission.to_dict() for permission in permissions],
            'total': len(permissions)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch permissions'}), 500

@bp.route('/permissions', methods=['POST'])
@require_permission('permissions:create')
def create_permission():
    """Create new permission"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        data = request.get_json()
        
        required_fields = ['name', 'description', 'resource', 'action']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'message': 'All fields are required: name, description, resource, action'}), 400
        
        name = data['name'].strip()
        description = data['description'].strip()
        resource = data['resource'].strip()
        action = data['action'].strip()
        
        # Check if permission already exists
        if Permission.query.filter_by(name=name).first():
            return jsonify({'message': 'Permission already exists'}), 409
        
        # Create new permission
        permission = Permission(name=name, description=description, resource=resource, action=action)
        db.session.add(permission)
        db.session.commit()
        
        log_audit_event(
            'permission_creation',
            f'Admin {current_user.username} created permission {name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'create_permission', 'permission_name': name, 'permission_id': permission.id}
        )
        
        return jsonify({
            'message': 'Permission created successfully',
            'permission': permission.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create permission'}), 500

@bp.route('/permissions/<int:permission_id>', methods=['PUT'])
@require_permission('permissions:update')
def update_permission(permission_id):
    """Update permission"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        permission = Permission.query.get_or_404(permission_id)
        data = request.get_json()
        
        old_name = permission.name
        
        if 'name' in data:
            permission.name = data['name'].strip()
        if 'description' in data:
            permission.description = data['description'].strip()
        if 'resource' in data:
            permission.resource = data['resource'].strip()
        if 'action' in data:
            permission.action = data['action'].strip()
        
        db.session.commit()
        
        log_audit_event(
            'permission_update',
            f'Admin {current_user.username} updated permission {old_name} to {permission.name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'update_permission', 'permission_id': permission_id, 'old_name': old_name, 'new_name': permission.name}
        )
        
        return jsonify({
            'message': 'Permission updated successfully',
            'permission': permission.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update permission'}), 500

@bp.route('/permissions/<int:permission_id>', methods=['DELETE'])
@require_permission('permissions:delete')
def delete_permission(permission_id):
    """Delete permission"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        permission = Permission.query.get_or_404(permission_id)
        
        # Check if permission is assigned to any roles
        if permission.roles:
            return jsonify({
                'message': f'Cannot delete permission. It is assigned to {len(permission.roles)} roles.'
            }), 400
        
        permission_name = permission.name
        db.session.delete(permission)
        db.session.commit()
        
        log_audit_event(
            'permission_deletion',
            f'Admin {current_user.username} deleted permission {permission_name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'delete_permission', 'permission_id': permission_id, 'permission_name': permission_name}
        )
        
        return jsonify({'message': 'Permission deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete permission'}), 500

# ====================
# ROLE-USER ASSIGNMENTS
# ====================

@bp.route('/users/<int:user_id>/roles', methods=['POST'])
@require_permission('users:update')
def assign_role(user_id):
    """Assign role to user"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        data = request.get_json()
        
        if not data or 'role_id' not in data:
            return jsonify({'message': 'Role ID is required'}), 400
        
        user = User.query.get_or_404(user_id)
        role = Role.query.get_or_404(data['role_id'])
        
        if role in user.roles:
            return jsonify({'message': 'Role already assigned to user'}), 409
        
        user.roles.append(role)
        db.session.commit()
        
        log_audit_event(
            'role_assignment',
            f'Admin {current_user.username} assigned role {role.name} to user {user.username}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'assign_role', 'target_user_id': user_id, 'target_username': user.username, 'role_id': role.id, 'role_name': role.name}
        )
        
        return jsonify({'message': 'Role assigned successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to assign role'}), 500

@bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@require_permission('users:update')
def revoke_role(user_id, role_id):
    """Revoke role from user"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        user = User.query.get_or_404(user_id)
        role = Role.query.get_or_404(role_id)
        
        if role not in user.roles:
            return jsonify({'message': 'Role not assigned to user'}), 409
        
        # Prevent removal of admin role from self
        if user.id == current_user.id and role.name == 'admin':
            return jsonify({'message': 'Cannot remove admin role from yourself'}), 400
        
        user.roles.remove(role)
        db.session.commit()
        
        log_audit_event(
            'role_revocation',
            f'Admin {current_user.username} revoked role {role.name} from user {user.username}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'revoke_role', 'target_user_id': user_id, 'target_username': user.username, 'role_id': role_id, 'role_name': role.name}
        )
        
        return jsonify({'message': 'Role revoked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to revoke role'}), 500

# ====================
# ROLE-PERMISSION ASSIGNMENTS
# ====================

@bp.route('/roles/<int:role_id>/permissions', methods=['POST'])
@require_permission('roles:update')
def assign_permission_to_role(role_id):
    """Assign permission to role"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        data = request.get_json()
        
        if not data or 'permission_id' not in data:
            return jsonify({'message': 'Permission ID is required'}), 400
        
        role = Role.query.get_or_404(role_id)
        permission = Permission.query.get_or_404(data['permission_id'])
        
        if permission in role.permissions:
            return jsonify({'message': 'Permission already assigned to role'}), 409
        
        role.permissions.append(permission)
        db.session.commit()
        
        log_audit_event(
            'permission_assignment',
            f'Admin {current_user.username} assigned permission {permission.name} to role {role.name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'assign_permission', 'role_id': role_id, 'role_name': role.name, 'permission_id': permission.id, 'permission_name': permission.name}
        )
        
        return jsonify({'message': 'Permission assigned to role successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to assign permission to role'}), 500

@bp.route('/roles/<int:role_id>/permissions/<int:permission_id>', methods=['DELETE'])
@require_permission('roles:update')
def revoke_permission_from_role(role_id, permission_id):
    """Revoke permission from role"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        role = Role.query.get_or_404(role_id)
        permission = Permission.query.get_or_404(permission_id)
        
        if permission not in role.permissions:
            return jsonify({'message': 'Permission not assigned to role'}), 409
        
        role.permissions.remove(permission)
        db.session.commit()
        
        log_audit_event(
            'permission_revocation',
            f'Admin {current_user.username} revoked permission {permission.name} from role {role.name}',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'revoke_permission', 'role_id': role_id, 'role_name': role.name, 'permission_id': permission_id, 'permission_name': permission.name}
        )
        
        return jsonify({'message': 'Permission revoked from role successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to revoke permission from role'}), 500

# ====================
# AUDIT LOGS ACCESS
# ====================

@bp.route('/audit-logs', methods=['GET'])
@require_permission('audit_logs:read')
def list_audit_logs():
    """List audit logs with filtering"""
    try:
        current_user, error_response, status_code = _get_authenticated_user()
        if error_response:
            return error_response, status_code
            
        # Query parameters for filtering
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id', type=int)
        success = request.args.get('success', type=bool)
        
        # Build query
        query = AuditLog.query
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if success is not None:
            query = query.filter(AuditLog.success == success)
        
        # Order by timestamp desc and paginate
        audit_logs = query.order_by(AuditLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        log_audit_event(
            'audit_access',
            f'Admin {current_user.username} accessed audit logs',
            True,
            user_id=current_user.id,
            username=current_user.username,
            metadata={'action': 'list_audit_logs', 'page': page, 'per_page': per_page}
        )
        
        return jsonify({
            'audit_logs': [log.to_dict() for log in audit_logs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': audit_logs.total,
                'pages': audit_logs.pages,
                'has_next': audit_logs.has_next,
                'has_prev': audit_logs.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch audit logs'}), 500 