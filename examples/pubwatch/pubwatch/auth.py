"""
Authentication and Authorization module for PubWatch
"""

import os
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import check_password_hash

# For demonstration purposes, we'll use a simple in-memory auth system
# In a production environment, this would be replaced with a proper database-backed system

# In-memory user storage for demo purposes (not suitable for production)
USERS = {
    "researcher1@example.com": {
        "password_hash": "pbkdf2:sha256:260000$example_hash_1",
        "role": "researcher",
    },
    "admin@example.com": {
        "password_hash": "pbkdf2:sha256:260000$example_hash_2",
        "role": "administrator",
    },
}


def generate_token(user_email):
    """Generate a JWT token for a user."""
    # In a real implementation, you'd use a proper secret key
    secret_key = os.getenv("SECRET_KEY", "default-secret-key-for-demo")

    payload = {
        "user_email": user_email,
        "role": USERS.get(user_email, {}).get("role", "researcher"),
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token


def verify_token(token):
    """Verify a JWT token."""
    try:
        secret_key = os.getenv("SECRET_KEY", "default-secret-key-for-demo")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication for endpoints."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization token"}), 401

        token = auth_header.split(" ")[1]
        payload = verify_token(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Add user info to request context
        request.current_user = payload.get("user_email")
        request.user_role = payload.get("role")

        return f(*args, **kwargs)

    return decorated_function


def require_role(role):
    """Decorator to require a specific role."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, "user_role") or request.user_role != role:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def authenticate_user(email, password):
    """Authenticate a user with email and password."""
    user = USERS.get(email)
    if not user:
        return False

    # In a real implementation, you'd compare the password hash
    # For demo purposes, we'll just verify it exists
    return True


def is_valid_user(user_email):
    """Check if user exists in our system."""
    return user_email in USERS
