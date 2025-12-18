"""
Authentication Handler for Finiquito Application
Manages user authentication and authorization
"""

import hashlib
from typing import Optional
from datetime import datetime
from infra.database.models import User
from infra.database.connection import get_db

def hash_password(password: str) -> str:
    """
    Hash a password using SHA256
    In production, use bcrypt or similar
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verify a password against stored hash
    For development, using plain comparison
    In production, use proper password hashing
    """
    # Development mode: plain text comparison
    if stored_password in ['admin123', 'oper123', 'view123']:
        return plain_password == stored_password
    
    # Production mode: hash comparison
    return hash_password(plain_password) == stored_password

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user by username and password
    Returns dict if successful, None otherwise
    """
    try:
        with get_db() as db:
            user = db.query(User).filter_by(username=username).first()
            
            if user and verify_password(password, user.password_hash):
                # Update last login
                user.last_login = datetime.utcnow()
                db.commit()
                
                # Retornar diccionario en lugar de objeto
                return {
                    'username': user.username,
                    'role': user.role.value if hasattr(user.role, 'value') else user.role,
                    'email': user.email,
                    'id': user.id
                }
            
            return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

def create_user(username: str, password: str, role: str, email: str = None, 
                created_by: str = 'system') -> Optional[User]:
    """
    Create a new user
    """
    try:
        with get_db() as db:
            # Check if user already exists
            existing = db.query(User).filter_by(username=username).first()
            if existing:
                return None
            
            # Create new user
            user = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                email=email,
                created_by=created_by
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def check_permission(user_role: str, required_permission: str) -> bool:
    """
    Check if a user role has a specific permission
    """
    # Permission matrix
    permissions = {
        'admin': [
            'view_all_cases',
            'edit_all_cases',
            'delete_cases',
            'manage_users',
            'manage_config',
            'manage_templates',
            'generate_documents',
            'approve_cases',
            'export_data'
        ],
        'operator': [
            'view_all_cases',
            'edit_own_cases',
            'generate_documents',
            'create_cases',
            'export_own_data'
        ],
        'viewer': [
            'view_all_cases',
            'view_reports'
        ]
    }
    
    user_permissions = permissions.get(user_role, [])
    return required_permission in user_permissions

def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID"""
    try:
        with get_db() as db:
            return db.query(User).filter_by(id=user_id).first()
    except Exception:
        return None

def get_all_users():
    """Get all users"""
    try:
        with get_db() as db:
            return db.query(User).all()
    except Exception:
        return []

def update_user_password(username: str, new_password: str) -> bool:
    """Update user password"""
    try:
        with get_db() as db:
            user = db.query(User).filter_by(username=username).first()
            if user:
                user.password_hash = hash_password(new_password)
                db.commit()
                return True
            return False
    except Exception:
        return False

def delete_user(username: str) -> bool:
    """Delete a user"""
    try:
        with get_db() as db:
            user = db.query(User).filter_by(username=username).first()
            if user:
                db.delete(user)
                db.commit()
                return True
            return False
    except Exception:
        return False
