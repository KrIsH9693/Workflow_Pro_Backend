import jwt
from flask import current_app
from flask_socketio import emit, join_room, leave_room
from extensions import db, socketio
from models.message_model import Message
from models.user_model import User
from models.workspace_model import Project

def authenticate_socket(token):
    if not token:
        return None
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return User.query.get(payload.get('user_id'))
    except Exception:
        return None

@socketio.on('join_project')
def handle_join_project(data):
    token = data.get('token')
    project_id = data.get('project_id')
    user = authenticate_socket(token)

    if not user or not project_id:
        emit('socket_error', {'error': 'Unauthorized or missing project_id.'})
        return

    # Multi-tenancy guard: check if project belongs to user's company
    project = Project.query.filter_by(id=project_id, company_id=user.company_id).first()
    if not project:
        emit('socket_error', {'error': 'Project access denied.'})
        return

    room = f"project_{project_id}"
    join_room(room)
    emit('user_joined', {
        'user_id': user.id,
        'user_name': user.full_name,
        'message': f"{user.full_name} is online in this project room."
    }, to=room)

@socketio.on('leave_project')
def handle_leave_project(data):
    project_id = data.get('project_id')
    if project_id:
        leave_room(f"project_{project_id}")

@socketio.on('send_message')
def handle_send_message(data):
    token = data.get('token')
    project_id = data.get('project_id')
    message_content = data.get('message', '').strip()

    user = authenticate_socket(token)
    if not user:
        emit('socket_error', {'error': 'Unauthorized token.'})
        return

    if not project_id or not message_content:
        emit('socket_error', {'error': 'Project ID and message cannot be empty.'})
        return

    # Check project tenancy
    project = Project.query.filter_by(id=project_id, company_id=user.company_id).first()
    if not project:
        emit('socket_error', {'error': 'Unauthorized project access.'})
        return

    # Save to Database using the exact column `message`
    new_msg = Message(
        company_id=user.company_id,
        project_id=project_id,
        sender_id=user.id,
        message=message_content
    )
    db.session.add(new_msg)
    db.session.commit()

    room = f"project_{project_id}"
    emit('receive_message', {
        'id': new_msg.id,
        'project_id': project_id,
        'message': new_msg.message,
        'sender': {
            'id': user.id,
            'name': user.full_name,
            'role': user.role.name
        },
        'created_at': new_msg.created_at.isoformat()
    }, to=room)