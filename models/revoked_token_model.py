from datetime import datetime
from extensions import db

class RevokedToken(db.Model):
    __tablename__ = 'RevokedTokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jti = db.Column(db.String(255), unique=True, nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)