from datetime import datetime
from extensions import db

class Workspace(db.Model):
    __tablename__ = 'Workspaces'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = db.relationship('Project', backref='workspace', lazy=True)


class Project(db.Model):
    __tablename__ = 'Projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    workspace_id = db.Column(db.Integer, db.ForeignKey('Workspaces.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='PLANNING')
    start_date = db.Column(db.Date, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = db.relationship('Task', backref='project', lazy=True)


class Task(db.Model):
    __tablename__ = 'Tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('Companies.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('Projects.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='TODO')
    priority = db.Column(db.String(50), default='MEDIUM')
    assigned_to = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)