from datetime import datetime
from extensions import db

class Message(db.Model):
    __tablename__ = 'Messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('Projects.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], lazy=True)
    project = db.relationship('Project', foreign_keys=[project_id], lazy=True)