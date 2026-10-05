from extensions import db
from models.comment_activity_model import ActivityLog

class ActivityService:
    @staticmethod
    def log(company_id, user_id, action, entity_type, entity_id=None, details=""):
        try:
            log_entry = ActivityLog(
                company_id=company_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[ACTIVITY LOG ERROR] {str(e)}")