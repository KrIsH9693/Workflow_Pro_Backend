from datetime import datetime
from extensions import db

class Notification(db.Model):
    __tablename__ = 'Notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    reference_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], lazy=True)