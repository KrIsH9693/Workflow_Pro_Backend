from datetime import datetime, date
from extensions import db
from models.workspace_model import Workspace, Project, Task
from models.user_model import User
from models.subtask_model import Subtask


class ProjectService:

    @classmethod
    def _is_admin(cls, user):
        return getattr(user.role, 'name', '') == 'Company Admin'

    @classmethod
    def create_project(cls, current_user, data):
        # RBAC: Only Company Admin can create projects
        if not cls._is_admin(current_user):
            return {'error': 'Unauthorized. Only Company Admins can create projects.'}, 403

        workspace_id = data.get('workspace_id')
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        status = data.get('status', 'PLANNING').strip().upper()
        manager_id = data.get('manager_id', current_user.id)
        start_date_str = data.get('start_date')
        deadline_str = data.get('deadline')

        if not workspace_id or not name:
            return {'error': 'Workspace ID and project name are required.'}, 400

        # Multi-tenancy check: Ensure workspace belongs to current user's company
        workspace = Workspace.query.filter_by(id=workspace_id, company_id=current_user.company_id).first()
        if not workspace:
            return {'error': 'Workspace not found in your company.'}, 404

        # Validate manager belongs to same company
        manager = User.query.filter_by(id=manager_id, company_id=current_user.company_id).first()
        if not manager:
            return {'error': 'Assigned project manager does not exist in your company.'}, 400

        start_date = None
        deadline = None
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if deadline_str:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            return {'error': 'Invalid date format. Use YYYY-MM-DD.'}, 400

        project = Project(
            company_id=current_user.company_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            status=status,
            manager_id=manager_id,
            start_date=start_date,
            deadline=deadline
        )
        db.session.add(project)
        db.session.commit()

        return {
            'message': 'Project created successfully.',
            'project': {
                'id': project.id,
                'company_id': project.company_id,
                'workspace_id': project.workspace_id,
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'manager_id': project.manager_id,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'deadline': project.deadline.isoformat() if project.deadline else None,
                'created_at': project.created_at.isoformat() if project.created_at else None
            }
        }, 201

    @classmethod
    def get_projects_by_workspace(cls, current_user, workspace_id):
        workspace = Workspace.query.filter_by(id=workspace_id, company_id=current_user.company_id).first()
        if not workspace:
            return {'error': 'Workspace not found in your company.'}, 404

        projects = Project.query.filter_by(workspace_id=workspace_id, company_id=current_user.company_id).all()
        result = []
        for p in projects:
            result.append({
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'status': p.status,
                'manager_id': p.manager_id,
                'start_date': p.start_date.isoformat() if p.start_date else None,
                'deadline': p.deadline.isoformat() if p.deadline else None,
                'task_count': len(p.tasks) if hasattr(p, 'tasks') else 0,
                'created_at': p.created_at.isoformat() if p.created_at else None
            })

        return {'projects': result}, 200

    @classmethod
    def create_task(cls, current_user, project_id, data):
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        status = data.get('status', 'TODO').strip().upper()
        priority = data.get('priority', 'MEDIUM').strip().upper()
        assigned_to = data.get('assigned_to')
        due_date_str = data.get('due_date')
        order_index = data.get('order_index', 0)

        if not title:
            return {'error': 'Task title is required.'}, 400

        project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first()
        if not project:
            return {'error': 'Project not found in your company.'}, 404

        if assigned_to:
            assignee = User.query.filter_by(id=assigned_to, company_id=current_user.company_id).first()
            if not assignee:
                return {'error': 'Assigned user does not belong to your company.'}, 400

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except ValueError:
                return {'error': 'Invalid due date format. Use ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD).'}, 400

        task = Task(
            company_id=current_user.company_id,
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            created_by=current_user.id,
            due_date=due_date,
            order_index=order_index
        )
        db.session.add(task)
        db.session.commit()

        return {
            'message': 'Task created successfully.',
            'task': {
                'id': task.id,
                'company_id': task.company_id,
                'project_id': task.project_id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'assigned_to': task.assigned_to,
                'created_by': task.created_by,
                'order_index': task.order_index,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'created_at': task.created_at.isoformat() if task.created_at else None
            }
        }, 201

    @classmethod
    def get_kanban_board(cls, current_user, project_id):
        project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first()
        if not project:
            return {'error': 'Project not found in your company.'}, 404

        tasks = Task.query.filter_by(project_id=project_id, company_id=current_user.company_id).order_by(Task.order_index.asc()).all()

        kanban = {
            'TODO': [],
            'IN_PROGRESS': [],
            'IN_REVIEW': [],
            'DONE': []
        }

        for t in tasks:
            col = t.status if t.status in kanban else 'TODO'
            assignee_data = None
            if t.assigned_to:
                u = User.query.get(t.assigned_to)
                if u:
                    assignee_data = {'id': u.id, 'name': u.full_name, 'email': u.email}

            kanban[col].append({
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'priority': t.priority,
                'order_index': t.order_index,
                'assignee': assignee_data,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'created_at': t.created_at.isoformat() if t.created_at else None
            })

        return {
            'project': {
                'id': project.id,
                'name': project.name,
                'status': project.status,
                'workspace_name': project.workspace.name if project.workspace else None
            },
            'board': kanban
        }, 200

    @classmethod
    def update_task_status_and_order(cls, current_user, task_id, data):
        new_status = data.get('status', '').strip().upper()
        new_order_index = data.get('order_index')

        task = Task.query.filter_by(id=task_id, company_id=current_user.company_id).first()
        if not task:
            return {'error': 'Task not found in your company.'}, 404

        valid_statuses = ['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE']
        if new_status and new_status not in valid_statuses:
            return {'error': f'Invalid status. Allowed: {", ".join(valid_statuses)}'}, 400

        # --- SMART WORKFLOW GATE ---
        is_admin = getattr(current_user.role, 'name', '') == 'Company Admin'
        if new_status == 'DONE' and not is_admin:
            return {
                'error': 'Unauthorized. Only Company Admins can approve and mark tasks as Done.'
            }, 403

        if not is_admin and task.assigned_to and task.assigned_to != current_user.id:
            return {
                'error': 'You can only update status for tasks assigned to you.'
            }, 403

        if new_status:
            task.status = new_status
        if new_order_index is not None:
            task.order_index = new_order_index

        db.session.commit()

        return {
            'message': 'Task updated successfully.',
            'task_id': task.id,
            'status': task.status,
            'order_index': task.order_index
        }, 200

    # -----------------------------------------------------------
    # SUBTASKS (CHECKLIST) SERVICE METHODS
    # -----------------------------------------------------------

    @classmethod
    def get_subtasks(cls, current_user, task_id):
        # Tenant isolation check
        task = Task.query.filter_by(id=task_id, company_id=current_user.company_id).first()
        if not task:
            return {'error': 'Task not found in your company.'}, 404

        subtasks = Subtask.query.filter_by(task_id=task_id).order_by(Subtask.created_at.asc()).all()
        return {
            'subtasks': [{
                'id': s.id,
                'task_id': s.task_id,
                'title': s.title,
                'is_completed': s.is_completed,
                'created_at': s.created_at.isoformat() if s.created_at else None
            } for s in subtasks]
        }, 200

    @classmethod
    def create_subtask(cls, current_user, task_id, data):
        title = data.get('title', '').strip()
        if not title:
            return {'error': 'Subtask title is required.'}, 400

        task = Task.query.filter_by(id=task_id, company_id=current_user.company_id).first()
        if not task:
            return {'error': 'Task not found in your company.'}, 404

        subtask = Subtask(
            task_id=task.id,
            title=title,
            is_completed=False
        )
        db.session.add(subtask)
        db.session.commit()

        return {
            'message': 'Subtask added successfully.',
            'subtask': {
                'id': subtask.id,
                'task_id': subtask.task_id,
                'title': subtask.title,
                'is_completed': subtask.is_completed,
                'created_at': subtask.created_at.isoformat()
            }
        }, 201

    @classmethod
    def toggle_subtask(cls, current_user, subtask_id):
        # Join check to ensure subtask's parent task belongs to user's company
        subtask = Subtask.query.join(Task, Subtask.task_id == Task.id).filter(
            Subtask.id == subtask_id,
            Task.company_id == current_user.company_id
        ).first()

        if not subtask:
            return {'error': 'Subtask not found in your company.'}, 404

        subtask.is_completed = not subtask.is_completed
        db.session.commit()

        return {
            'message': 'Subtask updated successfully.',
            'subtask': {
                'id': subtask.id,
                'is_completed': subtask.is_completed
            }
        }, 200

    @classmethod
    def delete_subtask(cls, current_user, subtask_id):
        # Join check for tenant security
        subtask = Subtask.query.join(Task, Subtask.task_id == Task.id).filter(
            Subtask.id == subtask_id,
            Task.company_id == current_user.company_id
        ).first()

        if not subtask:
            return {'error': 'Subtask not found in your company.'}, 404

        db.session.delete(subtask)
        db.session.commit()

        return {'message': 'Subtask deleted successfully.'}, 200