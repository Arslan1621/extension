from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    credits = db.Column(db.Integer, default=100)  # Free plan starts with 100 credits
    plan_type = db.Column(db.String(20), default='free')  # free, pro, premium
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def use_credit(self):
        """Use one credit for analysis"""
        if self.credits > 0:
            self.credits -= 1
            return True
        return False

    def add_credits(self, amount):
        """Add credits to user account"""
        self.credits += amount

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'credits': self.credits,
            'plan_type': self.plan_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }
