from flask import Blueprint, request, jsonify
from services.workspace_service import WorkspaceService
from utils.auth_decorators import token_required

workspace_bp = Blueprint('workspaces', __name__, url_prefix='/api/workspaces')

@workspace_bp.route('', methods=['POST'])
@token_required
def create_workspace(current_user):
    data = request.get_json() or {}
    response, status = WorkspaceService.create_workspace(current_user, data)
    return jsonify(response), status

@workspace_bp.route('', methods=['GET'])
@token_required
def get_all_workspaces(current_user):
    response, status = WorkspaceService.get_all_workspaces(current_user)
    return jsonify(response), status

@workspace_bp.route('/<int:workspace_id>', methods=['GET'])
@token_required
def get_workspace_by_id(current_user, workspace_id):
    response, status = WorkspaceService.get_workspace_by_id(current_user, workspace_id)
    return jsonify(response), status

@workspace_bp.route('/<int:workspace_id>', methods=['PUT'])
@token_required
def update_workspace(current_user, workspace_id):
    data = request.get_json() or {}
    response, status = WorkspaceService.update_workspace(current_user, workspace_id, data)
    return jsonify(response), status

@workspace_bp.route('/<int:workspace_id>', methods=['DELETE'])
@token_required
def delete_workspace(current_user, workspace_id):
    response, status = WorkspaceService.delete_workspace(current_user, workspace_id)
    return jsonify(response), status