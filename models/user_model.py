from datetime import datetime
from extensions import db

class Role(db.Model):
    __tablename__ = 'Roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='role', lazy=True)


class User(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('Roles.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(10), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_attempts = db.Column(db.Integer, default=0)
    verification_token = db.Column(db.String(255), nullable=True)
    reset_password_token = db.Column(db.String(255), nullable=True)
    refresh_token = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)