from datetime import datetime
from models.workspace_model import Workspace, Project, Task
from models.user_model import User

class DashboardService:

    @classmethod
    def get_dashboard_stats(cls, current_user):
        company_id = current_user.company_id
        is_admin = getattr(current_user.role, 'name', '') == 'Company Admin'
        now = datetime.utcnow()

        task_stats = {
            'TODO': 0,
            'IN_PROGRESS': 0,
            'IN_REVIEW': 0,
            'DONE': 0,
            'OVERDUE': 0
        }

        if is_admin:
            # --- COMPANY ADMIN VIEW (Complete Company Overview) ---
            total_workspaces = Workspace.query.filter_by(company_id=company_id).count()
            total_projects = Project.query.filter_by(company_id=company_id).count()
            total_members = User.query.filter_by(company_id=company_id, is_active=True).count()

            all_tasks = Task.query.filter_by(company_id=company_id).all()
            total_tasks = len(all_tasks)

            for t in all_tasks:
                if t.status in task_stats:
                    task_stats[t.status] += 1
                if t.due_date and t.due_date < now and t.status != 'DONE':
                    task_stats['OVERDUE'] += 1

            return {
                'role': 'Company Admin',
                'summary': {
                    'total_workspaces': total_workspaces,
                    'total_projects': total_projects,
                    'total_tasks': total_tasks,
                    'total_members': total_members
                },
                'task_breakdown': task_stats
            }, 200

        else:
            # --- TEAM MEMBER VIEW (Personalized My-Work View) ---
            # Sirf woh tasks jo is user ko assigned hain
            my_tasks = Task.query.filter_by(
                company_id=company_id,
                assigned_to=current_user.id
            ).all()
            
            total_my_tasks = len(my_tasks)

            for t in my_tasks:
                if t.status in task_stats:
                    task_stats[t.status] += 1
                if t.due_date and t.due_date < now and t.status != 'DONE':
                    task_stats['OVERDUE'] += 1

            # Projects jisme user ka koi task active hai
            assigned_project_ids = list({t.project_id for t in my_tasks if t.project_id})
            my_projects_count = len(assigned_project_ids)

            return {
                'role': 'Team Member',
                'summary': {
                    'total_workspaces': None, # Restricted for members
                    'total_projects': my_projects_count,
                    'total_tasks': total_my_tasks,
                    'total_members': None # Restricted for members
                },
                'task_breakdown': task_stats
            }, 200