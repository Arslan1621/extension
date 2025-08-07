from flask import Blueprint, request, jsonify
from src.models.user import db, User
from datetime import datetime
import re

user_bp = Blueprint('user', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Password is valid"

@user_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(name=name, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Account created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@user_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    """Get user profile"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile'}), 500

@user_bp.route('/use-credit/<int:user_id>', methods=['POST'])
def use_credit(user_id):
    """Use one credit for analysis"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.use_credit():
            db.session.commit()
            return jsonify({
                'message': 'Credit used successfully',
                'remaining_credits': user.credits
            }), 200
        else:
            return jsonify({'error': 'No credits remaining'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to use credit'}), 500

@user_bp.route('/add-credits/<int:user_id>', methods=['POST'])
def add_credits(user_id):
    """Add credits to user account"""
    try:
        data = request.get_json()
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return jsonify({'error': 'Invalid credit amount'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.add_credits(amount)
        db.session.commit()
        
        return jsonify({
            'message': f'{amount} credits added successfully',
            'total_credits': user.credits
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add credits'}), 500

@user_bp.route('/check-credits/<int:user_id>', methods=['GET'])
def check_credits(user_id):
    """Check user's remaining credits"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': user.id,
            'credits': user.credits,
            'plan_type': user.plan_type
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to check credits'}), 500

@user_bp.route('/upgrade-plan/<int:user_id>', methods=['POST'])
def upgrade_plan(user_id):
    """Upgrade user's plan"""
    try:
        data = request.get_json()
        new_plan = data.get('plan_type', '').lower()
        
        if new_plan not in ['free', 'pro', 'premium']:
            return jsonify({'error': 'Invalid plan type'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.plan_type = new_plan
        
        # Add credits based on plan
        if new_plan == 'pro':
            user.add_credits(500)  # Pro plan gets 500 additional credits
        elif new_plan == 'premium':
            user.add_credits(1000)  # Premium plan gets 1000 additional credits
        
        db.session.commit()
        
        return jsonify({
            'message': f'Plan upgraded to {new_plan}',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to upgrade plan'}), 500

@user_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'SmartFilter Auth API'}), 200