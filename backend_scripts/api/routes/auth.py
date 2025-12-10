"""
Authentication API Routes
Endpoints for user registration and login
"""

from flask import Blueprint, request, jsonify
import hashlib
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.db_helper import DatabaseHelper

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user
    
    POST /api/auth/register
    
    Request Body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "user_id": 1,
        "message": "User registered successfully"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate email format (basic)
        if '@' not in data['email']:
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters'
            }), 400
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        # Create user
        db = DatabaseHelper()
        user_id = db.create_user(
            name=data['name'],
            email=data['email'],
            password=hashed_password
        )
        db.close()
        
        if user_id:
            return jsonify({
                'success': True,
                'user_id': user_id,
                'message': 'User registered successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Email already exists'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    
    POST /api/auth/login
    
    Request Body:
    {
        "email": "john@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "user": {
            "user_id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        },
        "message": "Login successful"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        # Get user
        db = DatabaseHelper()
        user = db.get_user_by_email(data['email'])
        db.close()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Verify password
        if user['password'] != hashed_password:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Remove password from response
        user.pop('password', None)
        
        return jsonify({
            'success': True,
            'user': user,
            'message': 'Login successful'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

