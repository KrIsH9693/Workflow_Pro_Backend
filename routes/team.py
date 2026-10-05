from flask import Blueprint, request, jsonify
from services.team_service import TeamService
from utils.auth_decorators import token_required

team_bp = Blueprint('team', __name__, url_prefix='/api/team')

@team_bp.route('/invite', methods=['POST'])
@token_required
def invite_member(current_user):
    data = request.get_json() or {}
    response, status = TeamService.invite_member(current_user, data)
    return jsonify(response), status

@team_bp.route('/accept-invite', methods=['POST'])
def accept_invite():
    data = request.get_json() or {}
    response, status = TeamService.accept_invite(data)
    return jsonify(response), status

# Supports both /api/team and /api/team/members
@team_bp.route('', methods=['GET'])
@team_bp.route('/members', methods=['GET'])
@token_required
def get_team_members(current_user):
    response, status = TeamService.get_team_members(current_user)
    return jsonify(response), status

@team_bp.route('/members/<int:member_id>/role', methods=['PUT'])
@token_required
def update_member_role(current_user, member_id):
    data = request.get_json() or {}
    response, status = TeamService.update_member_role(current_user, member_id, data)
    return jsonify(response), status