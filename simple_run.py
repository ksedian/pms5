#!/usr/bin/env python3

# Simple Flask app to test the authentication system

from flask import Flask, request, jsonify
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# In-memory database simulation for testing
users_db = []
roles_db = [
    {'id': 1, 'name': 'worker', 'permissions': ['tasks:read', 'routes:read']},
    {'id': 2, 'name': 'engineer', 'permissions': ['tasks:create', 'tasks:read', 'tasks:update', 'routes:read']},
    {'id': 3, 'name': 'manager', 'permissions': ['tasks:*', 'routes:*', 'reports:read']},
    {'id': 4, 'name': 'admin', 'permissions': ['*:*']}
]

def hash_password(password):
    """Simple password hashing"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        salt, hash_hex = hashed.split(':')
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == hash_hex
    except:
        return False

def find_user_by_username(username):
    """Find user by username"""
    return next((user for user in users_db if user['username'] == username), None)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'MES Authentication'}), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip()
        password = data['password']
        
        # Basic validation
        if len(username) < 3 or len(username) > 80:
            return jsonify({'message': 'Username must be between 3 and 80 characters'}), 400
        
        if len(password) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long'}), 400
        
        # Check if user already exists
        if find_user_by_username(username):
            return jsonify({'message': 'Username already exists'}), 409
        
        if any(user['email'] == email for user in users_db):
            return jsonify({'message': 'Email already exists'}), 409
        
        # Create new user
        user = {
            'id': len(users_db) + 1,
            'username': username,
            'email': email,
            'password_hash': hash_password(password),
            'role_id': 1,  # Default to worker role
            'is_active': True,
            'failed_attempts': 0,
            'locked_until': None,
            'created_at': datetime.utcnow().isoformat()
        }
        
        users_db.append(user)
        
        # Remove sensitive data from response
        user_response = {k: v for k, v in user.items() if k != 'password_hash'}
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user_response
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({'message': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        user = find_user_by_username(username)
        
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not user['is_active']:
            return jsonify({'message': 'Account is inactive'}), 403
        
        # Check if account is locked
        if user['locked_until'] and datetime.fromisoformat(user['locked_until']) > datetime.utcnow():
            return jsonify({'message': 'Account is locked due to too many failed attempts'}), 423
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            user['failed_attempts'] += 1
            if user['failed_attempts'] >= 5:
                user['locked_until'] = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Reset failed attempts on successful login
        user['failed_attempts'] = 0
        user['locked_until'] = None
        
        # Get user role and permissions
        role = next((r for r in roles_db if r['id'] == user['role_id']), None)
        
        user_response = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': role['name'] if role else 'worker',
            'permissions': role['permissions'] if role else []
        }
        
        return jsonify({
            'message': 'Login successful',
            'user': user_response
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed'}), 500

@app.route('/api/admin/users', methods=['GET'])
def list_users():
    """List all users"""
    try:
        users_response = []
        for user in users_db:
            role = next((r for r in roles_db if r['id'] == user['role_id']), None)
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': role['name'] if role else 'worker',
                'is_active': user['is_active'],
                'failed_attempts': user['failed_attempts'],
                'created_at': user['created_at']
            }
            users_response.append(user_data)
        
        return jsonify({'users': users_response}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch users'}), 500

@app.route('/api/admin/roles', methods=['GET'])
def list_roles():
    """List all roles"""
    return jsonify({'roles': roles_db}), 200

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    admin_user = find_user_by_username('admin')
    if not admin_user:
        admin = {
            'id': len(users_db) + 1,
            'username': 'admin',
            'email': 'admin@mes.local',
            'password_hash': hash_password('AdminPassword123!'),
            'role_id': 4,  # Admin role
            'is_active': True,
            'failed_attempts': 0,
            'locked_until': None,
            'created_at': datetime.utcnow().isoformat()
        }
        users_db.append(admin)
        print("Admin user created: admin / AdminPassword123!")

if __name__ == '__main__':
    print("Starting MES Authentication Service...")
    print("Creating default admin user...")
    create_admin_user()
    print("\nAvailable endpoints:")
    print("- GET  /api/health                - Health check")
    print("- POST /api/auth/register         - Register new user")
    print("- POST /api/auth/login            - Login user")
    print("- GET  /api/admin/users           - List users")
    print("- GET  /api/admin/roles           - List roles")
    print("\nStarting server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 