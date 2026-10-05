import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from extensions import db
from models.attachment_model import Attachment
from models.workspace_model import Task, Project

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'xlsx', 'txt', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class AttachmentService:

    @classmethod
    def upload_file(cls, current_user, file, task_id=None, project_id=None):
        if not file or file.filename == '':
            return {'error': 'No file selected for upload.'}, 400

        if not allowed_file(file.filename):
            return {'error': 'File format not supported.'}, 400

        # Validate task or project scope with company isolation
        if task_id:
            task = Task.query.filter_by(id=task_id, company_id=current_user.company_id).first()
            if not task:
                return {'error': 'Task not found or unauthorized.'}, 404
            project_id = task.project_id
        elif project_id:
            project = Project.query.filter_by(id=project_id, company_id=current_user.company_id).first()
            if not project:
                return {'error': 'Project not found or unauthorized.'}, 404
        else:
            return {'error': 'Either task_id or project_id must be provided.'}, 400

        orig_filename = secure_filename(file.filename)
        ext = orig_filename.rsplit('.', 1)[1].lower() if '.' in orig_filename else ''
        unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

        company_folder = f"company_{current_user.company_id}"
        upload_folder = os.path.join(current_app.root_path, 'uploads', company_folder)
        os.makedirs(upload_folder, exist_ok=True)

        destination_path = os.path.join(upload_folder, unique_name)
        file.save(destination_path)
        file_size = os.path.getsize(destination_path)

        relative_file_path = os.path.join(company_folder, unique_name)

        attachment = Attachment(
            company_id=current_user.company_id,
            task_id=task_id,
            project_id=project_id,
            uploaded_by=current_user.id,
            file_name=orig_filename,
            file_path=relative_file_path,
            file_size=file_size,
            file_type=file.content_type
        )

        db.session.add(attachment)
        db.session.commit()

        return {
            'message': 'File uploaded successfully.',
            'attachment': {
                'id': attachment.id,
                'file_name': attachment.file_name,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
                'created_at': attachment.created_at.isoformat() if hasattr(attachment, 'created_at') and attachment.created_at else None
            }
        }, 201

    @classmethod
    def get_attachments_by_task(cls, current_user, task_id):
        attachments = Attachment.query.filter_by(company_id=current_user.company_id, task_id=task_id).all()
        return {
            'attachments': [{
                'id': a.id,
                'file_name': a.file_name,
                'filename': a.file_name,  # Dono keys provide kar di taaki frontend mismatch na ho
                'file_size': a.file_size,
                'file_type': a.file_type,
                'uploaded_by': a.uploader.full_name if hasattr(a, 'uploader') and a.uploader else 'Unknown',
                'created_at': a.created_at.isoformat() if hasattr(a, 'created_at') and a.created_at else None
            } for a in attachments]
        }, 200

    @classmethod
    def get_file_for_download(cls, current_user, attachment_id):
        attachment = Attachment.query.filter_by(id=attachment_id, company_id=current_user.company_id).first()
        if not attachment:
            return None, None, ({'error': 'File not found or unauthorized.'}, 404)

        full_path = os.path.join(current_app.root_path, 'uploads', attachment.file_path)
        if not os.path.exists(full_path):
            return None, None, ({'error': 'Physical file missing from storage.'}, 404)

        return full_path, attachment.file_name, None

    @classmethod
    def delete_attachment(cls, current_user, attachment_id):
        # 1. Company check zaroori hai
        attachment = Attachment.query.filter_by(id=attachment_id, company_id=current_user.company_id).first()
        if not attachment:
            return {'error': 'Attachment not found or unauthorized.'}, 404

        # 2. Correct full path resolution
        if attachment.file_path:
            full_path = os.path.join(current_app.root_path, 'uploads', attachment.file_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    print(f"Warning: Could not remove disk file: {e}")

        # 3. DB delete
        try:
            db.session.delete(attachment)
            db.session.commit()
            return {'message': 'Attachment deleted successfully.'}, 200
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete attachment: {str(e)}'}, 500