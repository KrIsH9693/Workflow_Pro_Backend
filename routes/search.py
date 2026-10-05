from flask import Blueprint, request, jsonify
from services.search_service import SearchService
from utils.auth_decorators import token_required

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

# 1. Global Search (Projects, Tasks, Members)
@search_bp.route('', methods=['GET'])
@token_required
def global_search(current_user):
    query_str = request.args.get('q', '').strip()
    response, status = SearchService.global_search(current_user, query_str)
    return jsonify(response), status

# 2. Advanced Task Filters
@search_bp.route('/tasks', methods=['GET'])
@token_required
def filter_tasks(current_user):
    filters = {
        'project_id': request.args.get('project_id', type=int),
        'status': request.args.get('status'),
        'priority': request.args.get('priority'),
        'assigned_to': request.args.get('assigned_to', type=int)
    }
    response, status = SearchService.filter_tasks(current_user, filters)
    return jsonify(response), status