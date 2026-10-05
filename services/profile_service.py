from extensions import db
from models.user_model import User
from werkzeug.security import generate_password_hash, check_password_hash

class ProfileService:

    @classmethod
    def get_profile(cls, current_user):
        return {
            'user': {
                'id': current_user.id,
                'full_name': current_user.full_name,
                'email': current_user.email,
                'role': current_user.role.name if current_user.role else 'Member',
                'company_id': current_user.company_id,
                'created_at': current_user.created_at.isoformat() if hasattr(current_user, 'created_at') and current_user.created_at else None
            }
        }, 200

    @classmethod
    def update_profile(cls, current_user, data):
        full_name = data.get('full_name', '').strip()

        if full_name:
            current_user.full_name = full_name

        try:
            db.session.commit()
            return {
                'message': 'Profile updated successfully.',
                'user': {
                    'id': current_user.id,
                    'full_name': current_user.full_name,
                    'email': current_user.email,
                    'role': current_user.role.name if current_user.role else 'Member'
                }
            }, 200
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update profile: {str(e)}'}, 500

    @classmethod
    def change_password(cls, current_user, data):
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')

        if not current_password or not new_password:
            return {'error': 'Current password and new password are required.'}, 400

        # Verify old password
        if not check_password_hash(current_user.password_hash, current_password):
            return {'error': 'Incorrect current password.'}, 400

        if len(new_password) < 6:
            return {'error': 'New password must be at least 6 characters long.'}, 400

        if new_password != confirm_password:
            return {'error': 'New password and confirmation do not match.'}, 400

        try:
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            return {'message': 'Password changed successfully. Please log in with your new password.'}, 200
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update password: {str(e)}'}, 500