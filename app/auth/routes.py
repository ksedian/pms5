from app.auth import bp
from app import db
from app.models import User, Role
from flask import request, jsonify
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
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed'}), 500 