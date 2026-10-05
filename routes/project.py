from flask import Blueprint, request, jsonify
from services.project_service import ProjectService
from models.workspace_model import Project, Task
from models.user_model import User
from utils.auth_decorators import token_required

project_bp = Blueprint('projects', __name__, url_prefix='/api')

# 1. Get All Team Members for Dropdown (/api/team)
@project_bp.route('/team', methods=['GET'])
@token_required
def get_company_team(current_user):
    members = User.query.filter_by(company_id=current_user.company_id, is_active=True).all()
    return jsonify({
        'members': [{
            'id': u.id,
            'name': u.full_name,
            'email': u.email
        } for u in members]
    }), 200

# 2. Get All Company Projects
@project_bp.route('/projects', methods=['GET'])
@token_required
def get_all_company_projects(current_user):
    projects = Project.query.filter_by(company_id=current_user.company_id).all()
    return jsonify({
        'projects': [{
            'id': p.id,
            'workspace_id': p.workspace_id,
            'name': p.name,
            'description': p.description,
            'status': p.status,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in projects]
    }), 200

# 3. Create Project
@project_bp.route('/projects', methods=['POST'])
@project_bp.route('/workspaces/<int:workspace_id>/projects', methods=['POST'])
@token_required
def create_project(current_user, workspace_id=None):
    data = request.get_json() or {}
    if workspace_id:
        data['workspace_id'] = workspace_id
    response, status = ProjectService.create_project(current_user, data)
    return jsonify(response), status

# 4. Get Projects by Workspace
@project_bp.route('/projects/workspace/<int:workspace_id>', methods=['GET'])
@project_bp.route('/workspaces/<int:workspace_id>/projects', methods=['GET'])
@token_required
def get_projects(current_user, workspace_id):
    response, status = ProjectService.get_projects_by_workspace(current_user, workspace_id)
    return jsonify(response), status

# 5. Tasks Endpoint (GET Kanban & POST Create Task)
@project_bp.route('/projects/<int:project_id>/tasks', methods=['GET', 'POST'])
@token_required
def handle_project_tasks(current_user, project_id):
    if request.method == 'GET':
        response, status = ProjectService.get_kanban_board(current_user, project_id)
        
        flat_tasks = []
        if isinstance(response, dict) and 'board' in response:
            board_data = response['board']
            for col_name, task_list in board_data.items():
                if isinstance(task_list, list):
                    for item in task_list:
                        item['status'] = col_name
                        flat_tasks.append(item)
            return jsonify({'tasks': flat_tasks, 'board': board_data, 'project': response.get('project')}), status

        return jsonify(response), status

    # POST (Create Task)
    data = request.get_json() or {}
    response, status = ProjectService.create_task(current_user, project_id, data)
    return jsonify(response), status

# 6. Update Task Status & Position (PATCH)
@project_bp.route('/projects/tasks/<int:task_id>', methods=['PATCH'])
@token_required
def update_task_status_order(current_user, task_id):
    data = request.get_json() or {}
    response, status = ProjectService.update_task_status_and_order(current_user, task_id, data)
    return jsonify(response), status

# 7. Subtasks Management Endpoints (GET & POST)
@project_bp.route('/tasks/<int:task_id>/subtasks', methods=['GET', 'POST'])
@token_required
def handle_subtasks(current_user, task_id):
    if request.method == 'GET':
        response, status = ProjectService.get_subtasks(current_user, task_id)
        return jsonify(response), status

    data = request.get_json() or {}
    response, status = ProjectService.create_subtask(current_user, task_id, data)
    return jsonify(response), status

# 8. Toggle Subtask Completion (PATCH)
@project_bp.route('/subtasks/<int:subtask_id>/toggle', methods=['PATCH'])
@token_required
def toggle_subtask_status(current_user, subtask_id):
    response, status = ProjectService.toggle_subtask(current_user, subtask_id)
    return jsonify(response), status

# 9. Delete Subtask (DELETE)
@project_bp.route('/subtasks/<int:subtask_id>', methods=['DELETE'])
@token_required
def remove_subtask(current_user, subtask_id):
    response, status = ProjectService.delete_subtask(current_user, subtask_id)
    return jsonify(response), status