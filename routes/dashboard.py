from flask import Blueprint, jsonify
from services.dashboard_service import DashboardService
from utils.auth_decorators import token_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('', methods=['GET'])
@dashboard_bp.route('/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    response, status = DashboardService.get_dashboard_stats(current_user)
    return jsonify(response), status