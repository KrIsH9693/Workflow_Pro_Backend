from extensions import db
from models.workspace_model import Workspace, Project, Task

class WorkspaceService:

    @classmethod
    def _is_admin(cls, user):
        return getattr(user.role, 'name', '') == 'Company Admin'

    @classmethod
    def create_workspace(cls, user, data):
        # RBAC: Only Company Admin can create workspaces
        if not cls._is_admin(user):
            return {'error': 'Unauthorized. Only Company Admins can create workspaces.'}, 403

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return {'error': 'Workspace name is required.'}, 400

        # Multi-tenant isolation: Check existing workspace in the SAME company
        existing = Workspace.query.filter_by(company_id=user.company_id, name=name).first()
        if existing:
            return {'error': 'A workspace with this name already exists in your company.'}, 409

        workspace = Workspace(
            company_id=user.company_id,
            name=name,
            description=description,
            created_by=user.id
        )
        db.session.add(workspace)
        db.session.commit()

        return {
            'message': 'Workspace created successfully.',
            'workspace': {
                'id': workspace.id,
                'name': workspace.name,
                'description': workspace.description,
                'created_by': workspace.created_by,
                'created_at': workspace.created_at.isoformat() if workspace.created_at else None
            }
        }, 201

    @classmethod
    def get_all_workspaces(cls, user):
        # Read-only access allowed for both Admin & Team Members of the company
        workspaces = Workspace.query.filter_by(company_id=user.company_id).all()

        result = []
        for ws in workspaces:
            result.append({
                'id': ws.id,
                'name': ws.name,
                'description': ws.description,
                'created_by': ws.created_by,
                'project_count': len(ws.projects) if hasattr(ws, 'projects') else 0,
                'created_at': ws.created_at.isoformat() if ws.created_at else None
            })

        return {'workspaces': result}, 200

    @classmethod
    def get_workspace_by_id(cls, user, workspace_id):
        workspace = Workspace.query.filter_by(id=workspace_id, company_id=user.company_id).first()
        if not workspace:
            return {'error': 'Workspace not found or access denied.'}, 404

        return {
            'workspace': {
                'id': workspace.id,
                'name': workspace.name,
                'description': workspace.description,
                'created_by': workspace.created_by,
                'created_at': workspace.created_at.isoformat() if workspace.created_at else None
            }
        }, 200

    @classmethod
    def update_workspace(cls, user, workspace_id, data):
        # RBAC: Only Company Admin can edit workspace details
        if not cls._is_admin(user):
            return {'error': 'Unauthorized. Only Company Admins can edit workspaces.'}, 403

        workspace = Workspace.query.filter_by(id=workspace_id, company_id=user.company_id).first()
        if not workspace:
            return {'error': 'Workspace not found or access denied.'}, 404

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if name:
            existing = Workspace.query.filter(
                Workspace.company_id == user.company_id,
                Workspace.name == name,
                Workspace.id != workspace_id
            ).first()
            if existing:
                return {'error': 'Another workspace with this name already exists.'}, 409
            workspace.name = name

        if description is not None:
            workspace.description = description

        db.session.commit()

        return {
            'message': 'Workspace updated successfully.',
            'workspace': {
                'id': workspace.id,
                'name': workspace.name,
                'description': workspace.description
            }
        }, 200

    @classmethod
    def delete_workspace(cls, user, workspace_id):
        # RBAC: Only Company Admin can delete workspaces
        if not cls._is_admin(user):
            return {'error': 'Unauthorized. Only Company Admins can delete workspaces.'}, 403

        workspace = Workspace.query.filter_by(id=workspace_id, company_id=user.company_id).first()
        if not workspace:
            return {'error': 'Workspace not found or access denied.'}, 404

        db.session.delete(workspace)
        db.session.commit()

        return {'message': 'Workspace deleted successfully.'}, 200