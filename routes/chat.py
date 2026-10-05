from flask import Blueprint, request, jsonify
from extensions import db, socketio
from models.message_model import Message
from models.workspace_model import Project
from utils.auth_decorators import token_required

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# 1. Fetch Chat History (GET)
@chat_bp.route('/project/<int:project_id>/messages', methods=['GET'])
@token_required
def get_project_messages(current_user, project_id):
    project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first()
    if not project:
        return jsonify({'error': 'Project not found in your company.'}), 404

    messages = Message.query.filter_by(
        project_id=project_id,
        company_id=current_user.company_id
    ).order_by(Message.created_at.asc()).all()

    chat_history = [{
        'id': m.id,
        'message': m.message,
        'sender': {
            'id': m.sender.id,
            'name': m.sender.full_name,
            'role': m.sender.role.name if m.sender and m.sender.role else 'Member'
        },
        'created_at': m.created_at.isoformat() if m.created_at else None
    } for m in messages]

    return jsonify({
        'project_id': project_id,
        'total_messages': len(chat_history),
        'messages': chat_history
    }), 200


# 2. Send Message via REST API (POST)
@chat_bp.route('/project/<int:project_id>/messages', methods=['POST'])
@token_required
def send_project_message(current_user, project_id):
    data = request.get_json() or {}
    message_text = data.get('message', '').strip()

    if not message_text:
        return jsonify({'error': 'Message text is required.'}), 400

    project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first()
    if not project:
        return jsonify({'error': 'Project not found in your company.'}), 404

    # Save to database
    new_msg = Message(
        company_id=current_user.company_id,
        project_id=project_id,
        sender_id=current_user.id,
        message=message_text
    )
    db.session.add(new_msg)
    db.session.commit()

    message_payload = {
        'id': new_msg.id,
        'project_id': project_id,
        'message': new_msg.message,
        'sender': {
            'id': current_user.id,
            'name': current_user.full_name,
            'role': current_user.role.name if current_user.role else 'Member'
        },
        'created_at': new_msg.created_at.isoformat() if new_msg.created_at else None
    }

    # Broadcast to real-time socket room
    try:
        room = f"project_{project_id}"
        socketio.emit('receive_message', message_payload, to=room)
    except Exception as e:
        print(f"[SOCKET BROADCAST ERROR] {str(e)}")

    return jsonify({
        'message': 'Message sent successfully.',
        'data': message_payload
    }), 201