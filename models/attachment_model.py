import datetime
from extensions import db

class Attachment(db.Model):
    __tablename__ = 'Attachments'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('Tasks.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('Projects.id'), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in Bytes
    file_type = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    uploader = db.relationship('User', backref='uploaded_files', lazy=True)