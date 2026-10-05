from flask import Blueprint, request, jsonify
from extensions import db
from models.workspace_model import Task
from models.comment_activity_model import TaskComment, ActivityLog
from services.activity_service import ActivityService
from services.notification_service import NotificationService
from utils.auth_decorators import token_required

comment_bp = Blueprint('comments', __name__, url_prefix='/api')

# 1. Add Comment to Task
@comment_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
@token_required
def add_comment(current_user, task_id):
    task = Task.query.filter_by(id=task_id, company_id=current_user.company_id).first()
    if not task:
        return jsonify({'error': 'Task not found in your company.'}), 404

    data = request.get_json() or {}
    comment_text = data.get('comment', '').strip()
    if not comment_text:
        return jsonify({'error': 'Comment text is required.'}), 400

    comment = TaskComment(
        company_id=current_user.company_id,
        task_id=task_id,
        user_id=current_user.id,
        comment=comment_text
    )
    db.session.add(comment)
    db.session.commit()

    # Log Activity
    ActivityService.log(
        company_id=current_user.company_id,
        user_id=current_user.id,
        action='COMMENT_ADDED',
        entity_type='TASK',
        entity_id=task_id,
        details=f"{current_user.full_name} commented on task '{task.title}'"
    )

    # Trigger Real-Time Notification & Socket Broadcast
    # Case A: Notify Assignee if someone else comments
    if task.assigned_to and task.assigned_to != current_user.id:
        NotificationService.send(
            company_id=current_user.company_id,
            user_id=task.assigned_to,
            title=f"New Comment on '{task.title}'",
            message=f"{current_user.full_name}: {comment_text[:80]}",
            notif_type='COMMENT',
            reference_id=task.id
        )

    # Case B: Notify Task Creator if neither assignee nor commenter
    if task.created_by and task.created_by != current_user.id and task.created_by != task.assigned_to:
        NotificationService.send(
            company_id=current_user.company_id,
            user_id=task.created_by,
            title=f"New Comment on '{task.title}'",
            message=f"{current_user.full_name}: {comment_text[:80]}",
            notif_type='COMMENT',
            reference_id=task.id
        )

    return jsonify({
        'message': 'Comment added successfully.',
        'comment': {
            'id': comment.id,
            'task_id': comment.task_id,
            'comment': comment.comment,
            'user': {
                'id': current_user.id,
                'name': current_user.full_name,
                'role': current_user.role.name if current_user.role else 'Member'
            },
            'created_at': comment.created_at.isoformat()
        }
    }), 201


# 2. Get All Comments for a Task
@comment_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
@token_required
def get_task_comments(current_user, task_id):
    task = Task.query.filter_by(id=task_id, company_id=current_user.company_id).first()
    if not task:
        return jsonify({'error': 'Task not found in your company.'}), 404

    comments = TaskComment.query.filter_by(task_id=task_id, company_id=current_user.company_id)\
                                .order_by(TaskComment.created_at.asc()).all()

    return jsonify({
        'task_id': task_id,
        'total_comments': len(comments),
        'comments': [{
            'id': c.id,
            'comment': c.comment,
            'user': {
                'id': c.user.id,
                'name': c.user.full_name,
                'role': c.user.role.name if c.user and c.user.role else 'Member'
            },
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in comments]
    }), 200


# 3. Delete Comment (Only author or Company Admin can delete)
@comment_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, comment_id):
    comment = TaskComment.query.filter_by(id=comment_id, company_id=current_user.company_id).first()
    if not comment:
        return jsonify({'error': 'Comment not found.'}), 404

    is_admin = current_user.role.name == 'Company Admin'
    is_owner = comment.user_id == current_user.id

    if not (is_admin or is_owner):
        return jsonify({'error': 'Unauthorized to delete this comment.'}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'Comment deleted successfully.'}), 200


# 4. Get Company Activity / Audit Logs
@comment_bp.route('/activity-logs', methods=['GET'])
@token_required
def get_activity_logs(current_user):
    logs = ActivityLog.query.filter_by(company_id=current_user.company_id)\
                            .order_by(ActivityLog.created_at.desc()).limit(50).all()

    return jsonify({
        'total_logs': len(logs),
        'logs': [{
            'id': l.id,
            'action': l.action,
            'entity_type': l.entity_type,
            'entity_id': l.entity_id,
            'details': l.details,
            'user': {
                'id': l.user.id,
                'name': l.user.full_name
            } if l.user else None,
            'created_at': l.created_at.isoformat() if l.created_at else None
        } for l in logs]
    }), 200