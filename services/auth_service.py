import jwt
import bcrypt
import datetime
import random
import re
from flask import current_app
from extensions import db
from models.company_model import Company
from models.user_model import User, Role
from utils.email_service import EmailService

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

class AuthService:

    @staticmethod
    def generate_otp() -> str:
        """Generates a random 6-digit numeric OTP string."""
        return str(random.randint(100000, 999999))

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def generate_tokens(user: User):
        access_payload = {
            'user_id': user.id,
            'company_id': user.company_id,
            'role': user.role.name if user.role else 'Member',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        access_token = jwt.encode(access_payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

        refresh_payload = {
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }
        refresh_token = jwt.encode(refresh_payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

        user.refresh_token = refresh_token
        db.session.commit()

        return access_token, refresh_token

    @classmethod
    def register_company(cls, data):
        company_name = data.get('company_name', '').strip()
        full_name = data.get('full_name', '').strip() 
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not all([company_name, full_name, email, password]):
            return {'error': 'All fields are required.'}, 400

        # Email format validation
        if not re.match(EMAIL_REGEX, email):
            return {'error': 'Invalid email address format.'}, 400

        # Password strength validation
        if not re.match(PASSWORD_REGEX, password):
            return {
                'error': 'Password must be at least 8 characters long, include uppercase, lowercase, number, and a special character.'
            }, 400

        # Check existing user
        existing_user = User.query.filter_by(email=email).first()

        # Duplicate email block
        if existing_user and existing_user.is_verified:
            return {
                'error': 'An account with this email already exists. Please login.'
            }, 409

        # Cooldown check for unverified spamming (60 seconds)
        now = datetime.datetime.utcnow()
        if existing_user and existing_user.otp_expires_at:
            time_left = (existing_user.otp_expires_at - now).total_seconds()
            if time_left > 540:  # 600s total (10m) - 60s cooldown = 540s
                return {'error': 'Please wait 60 seconds before requesting another OTP.'}, 429

        slug = re.sub(r'[^a-zA-Z0-9]', '-', company_name.lower()).strip('-')
        if not slug:
            slug = f"company-{random.randint(1000, 9999)}"

        # Company lookup or create
        company = Company.query.filter_by(slug=slug).first()
        if not company:
            company = Company(name=company_name, slug=slug)
            db.session.add(company)
            db.session.flush()

        admin_role = Role.query.filter_by(name='Company Admin').first()
        if not admin_role:
            admin_role = Role(name='Company Admin', description='Full company administrator')
            db.session.add(admin_role)
            db.session.commit()

        otp = cls.generate_otp()
        otp_expiry = now + datetime.timedelta(minutes=10)

        if existing_user:
            # Re-initialize unverified user
            existing_user.company_id = company.id
            existing_user.full_name = full_name
            existing_user.password_hash = cls.hash_password(password)
            existing_user.otp_code = otp
            existing_user.otp_expires_at = otp_expiry
            existing_user.otp_attempts = 0
            user = existing_user
        else:
            user = User(
                company_id=company.id,
                role_id=admin_role.id,
                full_name=full_name,
                email=email,
                password_hash=cls.hash_password(password),
                is_verified=False,
                otp_code=otp,
                otp_expires_at=otp_expiry,
                otp_attempts=0
            )
            db.session.add(user)

        db.session.commit()

        # Trigger Email dispatch
        EmailService.send_otp_email(to_email=email, otp=otp, user_name=full_name, purpose="Account Verification")

        return {
            'message': 'Registration initiated. OTP sent to your email.',
            'email': email,
            'otp_preview_dev': otp
        }, 201

    @classmethod
    def resend_otp(cls, data):
        email = data.get('email', '').strip().lower()

        if not email or not re.match(EMAIL_REGEX, email):
            return {'error': 'A valid email is required.'}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return {'error': 'No account associated with this email.'}, 404

        if user.is_verified:
            return {'error': 'Account is already verified. Please login.'}, 400

        now = datetime.datetime.utcnow()
        if user.otp_expires_at:
            time_left = (user.otp_expires_at - now).total_seconds()
            if time_left > 540:
                return {'error': 'Please wait 60 seconds before requesting a new OTP.'}, 429

        otp = cls.generate_otp()
        user.otp_code = otp
        user.otp_expires_at = now + datetime.timedelta(minutes=10)
        user.otp_attempts = 0
        db.session.commit()

        # Send new OTP
        EmailService.send_otp_email(to_email=email, otp=otp, user_name=user.full_name, purpose="Account Verification")

        return {
            'message': 'New OTP generated successfully.',
            'email': email,
            'otp_preview_dev': otp
        }, 200

    @classmethod
    def verify_otp(cls, data):
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()

        if not email or not otp:
            return {'error': 'Email and OTP are required.'}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return {'error': 'User not found.'}, 404

        if user.is_verified:
            return {'error': 'Account is already verified. Please login.'}, 400

        now = datetime.datetime.utcnow()

        if user.otp_expires_at is None or user.otp_expires_at < now:
            return {'error': 'OTP has expired. Please request a new OTP.'}, 400

        # Brute-force protection: Max 5 attempts
        if user.otp_attempts >= 5:
            user.otp_code = None
            user.otp_expires_at = None
            db.session.commit()
            return {'error': 'Too many invalid attempts. OTP invalidated. Request a new one.'}, 429

        if user.otp_code != otp:
            user.otp_attempts += 1
            db.session.commit()
            remaining = 5 - user.otp_attempts
            return {'error': f'Invalid OTP. {remaining} attempt(s) remaining.'}, 400

        # Verified successfully
        user.is_verified = True
        user.otp_code = None
        user.otp_expires_at = None
        user.otp_attempts = 0
        db.session.commit()

        access_token, refresh_token = cls.generate_tokens(user)

        return {
            'message': 'Account verified successfully!',
            'user': {
                'id': user.id,
                'name': user.full_name,
                'email': user.email,
                'role': user.role.name if user.role else 'Member',
                'company_id': user.company_id
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 200

    @classmethod
    def login_user(cls, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return {'error': 'Email and password are required.'}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not cls.verify_password(password, user.password_hash):
            return {'error': 'Invalid email or password.'}, 401

        if not user.is_verified:
            return {'error': 'Account not verified. Please verify your email via OTP.'}, 403

        if not user.is_active:
            return {'error': 'Account is deactivated. Contact administrator.'}, 403

        access_token, refresh_token = cls.generate_tokens(user)

        return {
            'message': 'Login successful.',
            'user': {
                'id': user.id,
                'name': user.full_name,
                'email': user.email,
                'role': user.role.name if user.role else 'Member',
                'company_id': user.company_id
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 200

    @classmethod
    def forgot_password(cls, data: dict):
        email = data.get('email', '').strip().lower()
        if not email:
            return {'error': 'Email is required.'}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return {'message': 'If your email is registered, you will receive a reset OTP.'}, 200

        otp = cls.generate_otp()
        user.otp_code = otp
        user.otp_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        user.otp_attempts = 0
        db.session.commit()

        EmailService.send_otp_email(to_email=user.email, otp=otp, user_name=user.full_name, purpose="Password Reset")
        return {'message': 'Password reset OTP has been sent to your email.', 'otp_preview_dev': otp}, 200

    @classmethod
    def reset_password(cls, data: dict):
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '')

        if not email or not otp or not new_password:
            return {'error': 'Email, OTP, and new password are required.'}, 400

        if not re.match(PASSWORD_REGEX, new_password):
            return {
                'error': 'Password must be at least 8 characters long, include uppercase, lowercase, number, and a special character.'
            }, 400

        user = User.query.filter_by(email=email).first()
        if not user or user.otp_code != otp:
            return {'error': 'Invalid OTP or email.'}, 400

        if user.otp_expires_at and user.otp_expires_at < datetime.datetime.utcnow():
            return {'error': 'OTP has expired. Please request a new one.'}, 400

        user.password_hash = cls.hash_password(new_password)
        user.otp_code = None
        user.otp_expires_at = None
        user.otp_attempts = 0
        db.session.commit()

        return {'message': 'Password has been reset successfully. You can now log in.'}, 200