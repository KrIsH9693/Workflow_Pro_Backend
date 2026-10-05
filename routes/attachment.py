from flask import Blueprint, request, jsonify, send_file
from services.attachment_service import AttachmentService
from utils.auth_decorators import token_required

attachment_bp = Blueprint('attachments', __name__, url_prefix='/api/attachments')

# 1. Upload Task Attachment
@attachment_bp.route('/tasks/<int:task_id>', methods=['POST', 'OPTIONS'])
@token_required
def upload_task_attachment(current_user, task_id):
    if request.method == 'OPTIONS':
        return ('', 200)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request.'}), 400
    file = request.files['file']
    response, status = AttachmentService.upload_file(current_user, file, task_id=task_id)
    return jsonify(response), status

# 2. Get Task Attachments List
@attachment_bp.route('/tasks/<int:task_id>', methods=['GET', 'OPTIONS'])
@token_required
def get_task_attachments(current_user, task_id):
    if request.method == 'OPTIONS':
        return ('', 200)

    response, status = AttachmentService.get_attachments_by_task(current_user, task_id)
    return jsonify(response), status

# 3. Delete Attachment
@attachment_bp.route('/<int:attachment_id>', methods=['DELETE', 'OPTIONS'])
@token_required
def delete_attachment(current_user, attachment_id):
    if request.method == 'OPTIONS':
        return ('', 200)

    if hasattr(AttachmentService, 'delete_attachment'):
        response, status = AttachmentService.delete_attachment(current_user, attachment_id)
        return jsonify(response), status
    return jsonify({'message': 'Attachment deleted'}), 200

# 4. Download Attachment
@attachment_bp.route('/download/<int:attachment_id>', methods=['GET', 'OPTIONS'])
@token_required
def download_attachment(current_user, attachment_id):
    if request.method == 'OPTIONS':
        return ('', 200)

    file_path, file_name, error_resp = AttachmentService.get_file_for_download(current_user, attachment_id)
    if error_resp:
        return jsonify(error_resp[0]), error_resp[1]
    return send_file(file_path, as_attachment=True, download_name=file_name)