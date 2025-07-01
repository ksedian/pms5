from app.admin import bp
from app import db
from app.models import User, Role, Permission
from flask import request, jsonify

@bp.route('/users', methods=['GET'])
def list_users():
    """List all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch users'}), 500

@bp.route('/roles', methods=['GET'])
def list_roles():
    """List all roles"""
    try:
        roles = Role.query.all()
        return jsonify({
            'roles': [role.to_dict() for role in roles]
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch roles'}), 500

@bp.route('/permissions', methods=['GET'])
def list_permissions():
    """List all permissions"""
    try:
        permissions = Permission.query.all()
        return jsonify({
            'permissions': [permission.to_dict() for permission in permissions]
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch permissions'}), 500

@bp.route('/users/<int:user_id>/roles', methods=['POST'])
def assign_role(user_id):
    """Assign role to user"""
    try:
        data = request.get_json()
        if not data or 'role_id' not in data:
            return jsonify({'message': 'Role ID is required'}), 400
        
        user = User.query.get_or_404(user_id)
        role = Role.query.get_or_404(data['role_id'])
        
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()
        
        return jsonify({'message': 'Role assigned successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to assign role'}), 500 