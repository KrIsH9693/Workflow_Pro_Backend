from datetime import datetime
from extensions import db

class Company(db.Model):
    __tablename__ = 'Companies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    domain = db.Column(db.String(255), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = db.relationship('User', backref='company', lazy=True)
    workspaces = db.relationship('Workspace', backref='company', lazy=True)