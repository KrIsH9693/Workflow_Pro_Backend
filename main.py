import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from config import Config
from extensions import db, socketio
import models

# Blueprints
from routes.auth import auth_bp
from routes.workspace import workspace_bp
from routes.team import team_bp
from routes.project import project_bp
from routes.dashboard import dashboard_bp
from routes.chat import chat_bp
from routes.comment import comment_bp
from routes.notification import notification_bp
from routes.attachment import attachment_bp
from routes.search import search_bp
from routes.profile import profile_bp

# Sockets
import sockets.chat_socket

# Allowed origins for development and production
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for HTTP and Socket endpoints
    CORS(
        app,
        resources={r"/*": {"origins": ALLOWED_ORIGINS}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins=ALLOWED_ORIGINS)

    # Register all Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(workspace_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(attachment_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(profile_bp)

    # Preflight / OPTIONS CORS Header Hook
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin in ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response

    # ==========================================
    # GLOBAL EXCEPTION HANDLERS (HIDE SENSITIVE DATA)
    # ==========================================

    # 1. Database & SQLAlchemy Errors (Masks database passwords & URIs)
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        # Console me sanitized error record hoga, raw URI leak nahi hogi
        app.logger.error("Database operation failed: [Credentials Masked]")
        return jsonify({
            "status": "error",
            "error_type": "DatabaseError",
            "message": "A database connection or query issue occurred. Please try again later."
        }), 500

    # 2. Standard HTTP Exceptions (e.g., 404, 403, 400)
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            "status": "error",
            "code": error.code,
            "message": error.description
        }), error.code

    # 3. Catch-All Generic Internal Server Errors (500)
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.error(f"Unhandled Server Error: {str(error)}")
        return jsonify({
            "status": "error",
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred on the server."
        }), 500

    @app.route('/')
    def home():
        return {
            "status": "success", 
            "message": "WorkFlow Pro API & Real-Time Socket Server Running",
            "active_modules": ["auth", "workspaces", "team", "projects", "dashboard", "chat_sockets"]
        }, 200

    return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=False, host='127.0.0.1', port=5000)