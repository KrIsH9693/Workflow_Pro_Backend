import jwt
from functools import wraps
from flask import request, jsonify, current_app
from models.user_model import User
from models.revoked_token_model import RevokedToken

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. CORS Preflight request ko direct 200 pass hone dein
        if request.method == 'OPTIONS':
            return ('', 200)

        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing or invalid format. Use Bearer <token>'}), 401

        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            
            # Check if token was revoked (logged out)
            jti = payload.get('jti') or token[:250]
            if RevokedToken.query.filter_by(jti=jti).first():
                return jsonify({'error': 'Token has been revoked. Please log in again.'}), 401

            current_user = User.query.get(payload['user_id'])
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token signature'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            # Role check me safe access (agar role object ho ya direct string)
            role_name = getattr(current_user.role, 'name', current_user.role) if current_user.role else None
            if role_name not in allowed_roles:
                return jsonify({'error': 'Unauthorized: Insufficient permissions'}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator