from flask import Blueprint, request, jsonify
from services.profile_service import ProfileService
from utils.auth_decorators import token_required

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

# 1. Get Logged-in User Profile
@profile_bp.route('', methods=['GET'])
@token_required
def get_profile(current_user):
    response, status = ProfileService.get_profile(current_user)
    return jsonify(response), status

# 2. Update Basic Info (e.g. Full Name)
@profile_bp.route('', methods=['PATCH'])
@token_required
def update_profile(current_user):
    data = request.get_json() or {}
    response, status = ProfileService.update_profile(current_user, data)
    return jsonify(response), status

# 3. Change Password
@profile_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json() or {}
    response, status = ProfileService.change_password(current_user, data)
    return jsonify(response), status