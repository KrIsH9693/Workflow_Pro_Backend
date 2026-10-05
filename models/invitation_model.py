from datetime import datetime
from extensions import db

class Invitation(db.Model):
    __tablename__ = 'Invitations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('Roles.id'), nullable=False)
    invite_token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_accepted = db.Column(db.Boolean, default=False)
    invited_by = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company', backref='invitations', lazy=True)
    role = db.relationship('Role', lazy=True)
    sender = db.relationship('User', foreign_keys=[invited_by], lazy=True)