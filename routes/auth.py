import jwt
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.revoked_token_model import RevokedToken
from services.auth_service import AuthService
from utils.auth_decorators import token_required

# Safe bcrypt import (agar environment me ho)
try:
    import bcrypt
except ImportError:
    bcrypt = None

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# --- Password Helpers (Bcrypt + Werkzeug Safe Fallback) ---
def verify_user_password(user, raw_password: str) -> bool:
    """Check password against user model methods, bcrypt hashes, or werkzeug hashes."""
    # 1. Agar User model me already helper method ho (e.g. user.check_password)
    if hasattr(user, 'check_password') and callable(getattr(user, 'check_password')):
        try:
            return user.check_password(raw_password)
        except Exception:
            pass

    # 2. Database hash extract karein
    stored_hash = getattr(user, 'password_hash', None) or getattr(user, 'password', None)
    if not stored_hash:
        return False

    # 3. Bcrypt format ($2a$, $2b$, $2y$) check
    if isinstance(stored_hash, str) and stored_hash.startswith(('$2a$', '$2b$', '$2y$')):
        if bcrypt:
            try:
                return bcrypt.checkpw(raw_password.encode('utf-8'), stored_hash.encode('utf-8'))
            except Exception:
                return False
        # Agar bcrypt module na ho, try werkzeug
        try:
            return check_password_hash(stored_hash, raw_password)
        except Exception:
            return False

    # 4. Standard Werkzeug Hash check (scrypt, pbkdf2, etc.)
    try:
        return check_password_hash(stored_hash, raw_password)
    except Exception:
        # Fallback agar hash format me method empty ho
        if bcrypt:
            try:
                return bcrypt.checkpw(raw_password.encode('utf-8'), stored_hash.encode('utf-8'))
            except Exception:
                pass
        return False


def set_user_password(user, raw_password: str):
    """Hash and assign new password to user model correctly."""
    # 1. Agar User model me set_password method ho
    if hasattr(user, 'set_password') and callable(getattr(user, 'set_password')):
        user.set_password(raw_password)
        return

    # 2. Bcrypt agar preferred/available ho
    if bcrypt:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(raw_password.encode('utf-8'), salt).decode('utf-8')
    else:
        hashed = generate_password_hash(raw_password)

    if hasattr(user, 'password_hash'):
        user.password_hash = hashed
    else:
        user.password = hashed


# ================= ROUTES =================

# 1. Company Registration
@auth_bp.route('/register-company', methods=['POST'])
def register_company():
    data = request.get_json() or {}
    response, status = AuthService.register_company(data)
    return jsonify(response), status

# 2. Resend Registration OTP
@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = request.get_json() or {}
    response, status = AuthService.resend_otp(data)
    return jsonify(response), status

# 3. Verify Registration OTP
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json() or {}
    response, status = AuthService.verify_otp(data)
    return jsonify(response), status

# 4. User Login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    response, status = AuthService.login_user(data)
    return jsonify(response), status

# 5. Get Logged-in User Profile
@auth_bp.route('/me', methods=['GET', 'OPTIONS'])
@token_required
def get_current_user_profile(current_user):
    if request.method == 'OPTIONS':
        return ('', 200)

    role_name = getattr(current_user.role, 'name', current_user.role) if current_user.role else 'Member'

    return jsonify({
        'id': current_user.id,
        'name': current_user.full_name,
        'full_name': current_user.full_name,
        'email': current_user.email,
        'role': role_name,
        'company_id': current_user.company_id
    }), 200

# 6. Update User Profile Name
@auth_bp.route('/profile', methods=['PUT', 'OPTIONS'])
@token_required
def update_profile(current_user):
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()

    if not full_name:
        return jsonify({'error': 'Full name is required.'}), 400

    try:
        current_user.full_name = full_name
        db.session.commit()

        role_name = getattr(current_user.role, 'name', current_user.role) if current_user.role else 'Member'

        return jsonify({
            'message': 'Profile updated successfully.',
            'user': {
                'id': current_user.id,
                'name': current_user.full_name,
                'full_name': current_user.full_name,
                'email': current_user.email,
                'role': role_name
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

# 7. Change Password
@auth_bp.route('/change-password', methods=['POST', 'OPTIONS'])
@token_required
def change_password(current_user):
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if not current_password or not new_password:
        return jsonify({'error': 'Both current and new password are required.'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long.'}), 400

    # Robust Password Verification
    if not verify_user_password(current_user, current_password):
        return jsonify({'error': 'Current password is incorrect.'}), 400

    try:
        set_user_password(current_user, new_password)
        db.session.commit()
        return jsonify({'message': 'Password changed successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update password: {str(e)}'}), 500

# 8. Forgot Password (Send Reset OTP)
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    response, status = AuthService.forgot_password(data)
    return jsonify(response), status

# 9. Reset Password with OTP
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    response, status = AuthService.reset_password(data)
    return jsonify(response), status

# 10. User Logout (Blacklist current JWT)
@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
@token_required
def logout(current_user):
    if request.method == 'OPTIONS':
        return ('', 200)

    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(" ")[1] if " " in auth_header else auth_header
    
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        jti = payload.get('jti') or token[:250]
        
        revoked = RevokedToken(jti=jti)
        db.session.add(revoked)
        db.session.commit()
        return jsonify({'message': 'Logged out successfully. Token invalidated.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Logout failed.'}), 500