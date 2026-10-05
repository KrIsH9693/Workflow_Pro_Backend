from extensions import db, socketio
from models.notification_model import Notification

class NotificationService:
    @staticmethod
    def send(company_id, user_id, title, message, notif_type, reference_id=None):
        try:
            notif = Notification(
                company_id=company_id,
                user_id=user_id,
                title=title,
                message=message,
                type=notif_type,
                reference_id=reference_id
            )
            db.session.add(notif)
            db.session.commit()

            # Real-time socket broadcast if user is online
            try:
                socketio.emit(f'notification_user_{user_id}', {
                    'id': notif.id,
                    'title': notif.title,
                    'message': notif.message,
                    'type': notif.type,
                    'reference_id': notif.reference_id,
                    'created_at': notif.created_at.isoformat()
                })
            except Exception as se:
                print(f"[SOCKET NOTIF ERROR] {str(se)}")

            return notif
        except Exception as e:
            db.session.rollback()
            print(f"[NOTIFICATION ERROR] {str(e)}")
            return None