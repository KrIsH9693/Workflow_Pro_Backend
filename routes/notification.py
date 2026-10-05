from flask import Blueprint, jsonify
from extensions import db
from models.notification_model import Notification
from utils.auth_decorators import token_required

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# 1. Fetch User Notifications & Unread Count
@notification_bp.route('/', methods=['GET'])
@token_required
def get_notifications(current_user):
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        company_id=current_user.company_id
    ).order_by(Notification.created_at.desc()).limit(30).all()

    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        company_id=current_user.company_id,
        is_read=False
    ).count()

    return jsonify({
        'unread_count': unread_count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'reference_id': n.reference_id,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None
        } for n in notifications]
    }), 200


# 2. Mark Single Notification as Read
@notification_bp.route('/<int:notif_id>/read', methods=['PATCH'])
@token_required
def mark_as_read(current_user, notif_id):
    notif = Notification.query.filter_by(
        id=notif_id,
        user_id=current_user.id,
        company_id=current_user.company_id
    ).first()

    if not notif:
        return jsonify({'error': 'Notification not found.'}), 404

    notif.is_read = True
    db.session.commit()

    return jsonify({'message': 'Notification marked as read.'}), 200


# 3. Mark All Notifications as Read
@notification_bp.route('/read-all', methods=['PATCH'])
@token_required
def mark_all_as_read(current_user):
    Notification.query.filter_by(
        user_id=current_user.id,
        company_id=current_user.company_id,
        is_read=False
    ).update({'is_read': True})

    db.session.commit()
    return jsonify({'message': 'All notifications marked as read.'}), 200