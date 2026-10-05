from datetime import datetime
from extensions import db

class TaskComment(db.Model):
    __tablename__ = 'TaskComments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('Tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], lazy=True)
    task = db.relationship('Task', foreign_keys=[task_id], lazy=True)


class ActivityLog(db.Model):
    __tablename__ = 'ActivityLogs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], lazy=True)