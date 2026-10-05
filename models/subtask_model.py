from datetime import datetime
from extensions import db

class Subtask(db.Model):
    __tablename__ = 'Subtasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('Tasks.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = db.relationship('Task', backref=db.backref('subtasks', cascade='all, delete-orphan', lazy=True))