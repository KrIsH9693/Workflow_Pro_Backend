from sqlalchemy import or_
from models.workspace_model import Project, Task, Workspace
from models.user_model import User

class SearchService:

    @classmethod
    def global_search(cls, current_user, query_str):
        if not query_str or len(query_str.strip()) < 2:
            return {'error': 'Search query must be at least 2 characters long.'}, 400

        q = f"%{query_str.strip()}%"
        company_id = current_user.company_id

        # 1. Search Projects
        projects = Project.query.filter(
            Project.company_id == company_id,
            or_(Project.name.ilike(q), Project.description.ilike(q))
        ).limit(10).all()

        # 2. Search Tasks
        tasks = Task.query.filter(
            Task.company_id == company_id,
            or_(Task.title.ilike(q), Task.description.ilike(q))
        ).limit(15).all()

        # 3. Search Team Members
        members = User.query.filter(
            User.company_id == company_id,
            User.is_active == True,
            or_(User.full_name.ilike(q), User.email.ilike(q))
        ).limit(10).all()

        return {
            'query': query_str,
            'results': {
                'projects': [{
                    'id': p.id,
                    'name': p.name,
                    'status': p.status,
                    'workspace_id': p.workspace_id
                } for p in projects],
                'tasks': [{
                    'id': t.id,
                    'title': t.title,
                    'status': t.status,
                    'priority': t.priority,
                    'project_id': t.project_id
                } for t in tasks],
                'members': [{
                    'id': m.id,
                    'full_name': m.full_name,
                    'email': m.email,
                    'role': m.role.name if m.role else 'Member'
                } for m in members]
            }
        }, 200

    @classmethod
    def filter_tasks(cls, current_user, filters):
        company_id = current_user.company_id
        query = Task.query.filter_by(company_id=company_id)

        project_id = filters.get('project_id')
        status = filters.get('status')
        priority = filters.get('priority')
        assigned_to = filters.get('assigned_to')

        if project_id:
            query = query.filter(Task.project_id == project_id)
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if assigned_to:
            query = query.filter(Task.assigned_to == assigned_to)

        tasks = query.order_by(Task.created_at.desc()).all()

        return {
            'total': len(tasks),
            'tasks': [{
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'project_id': t.project_id,
                'assigned_to': t.assigned_to,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'created_at': t.created_at.isoformat() if t.created_at else None
            } for t in tasks]
        }, 200