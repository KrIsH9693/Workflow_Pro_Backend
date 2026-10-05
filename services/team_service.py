import secrets
import datetime
import re
from extensions import db
from models.user_model import User, Role
from models.invitation_model import Invitation
from models.company_model import Company
from services.auth_service import AuthService, EMAIL_REGEX, PASSWORD_REGEX
from utils.email_service import EmailService

class TeamService:

    @classmethod
    def invite_member(cls, current_user, data):
        # RBAC Check: Only Admin can invite
        if current_user.role.name != 'Company Admin':
            return {'error': 'Unauthorized. Only Company Admins can invite team members.'}, 403

        email = data.get('email', '').strip().lower()
        role_name = data.get('role_name', 'Team Member').strip()

        if not email or not re.match(EMAIL_REGEX, email):
            return {'error': 'A valid email address is required.'}, 400

        # Check if already a verified user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.is_verified:
            return {'error': 'User with this email is already registered.'}, 409

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return {'error': f'Role {role_name} does not exist.'}, 400

        # Generate secure invite token (24 hours expiry)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

        # Invalidate old pending invites for this email
        Invitation.query.filter_by(company_id=current_user.company_id, email=email, is_accepted=False).delete()

        invitation = Invitation(
            company_id=current_user.company_id,
            email=email,
            role_id=role.id,
            invite_token=token,
            expires_at=expires_at,
            invited_by=current_user.id
        )
        db.session.add(invitation)
        db.session.commit()

        # Company details lookup
        company = Company.query.get(current_user.company_id)
        company_name = company.name if company else "Our Team"

        # Trigger Real SMTP Email Dispatch
        EmailService.send_invite_email(
            to_email=email,
            invite_token=token,
            company_name=company_name,
            invited_by_name=current_user.full_name,
            role_name=role.name
        )

        return {
            'message': f'Invitation successfully sent to {email}.',
            'invite_token_preview_dev': token,
            'expires_at': expires_at.isoformat()
        }, 201

    @classmethod
    def accept_invite(cls, data):
        token = data.get('token', '').strip()
        full_name = data.get('full_name', '').strip()
        password = data.get('password', '')

        if not token or not full_name or not password:
            return {'error': 'Token, full name, and password are required.'}, 400

        if not re.match(PASSWORD_REGEX, password):
            return {
                'error': 'Password must be at least 8 characters long, include uppercase, lowercase, number, and a special character.'
            }, 400

        invitation = Invitation.query.filter_by(invite_token=token).first()
        if not invitation:
            return {'error': 'Invalid invitation token.'}, 404

        if invitation.is_accepted:
            return {'error': 'This invitation has already been accepted. Please login.'}, 400

        if invitation.expires_at < datetime.datetime.utcnow():
            return {'error': 'Invitation link has expired. Request a new invite from your Admin.'}, 400

        # Create or activate user
        existing_user = User.query.filter_by(email=invitation.email).first()
        if existing_user:
            user = existing_user
            user.company_id = invitation.company_id
            user.role_id = invitation.role_id
            user.full_name = full_name
            user.password_hash = AuthService.hash_password(password)
            user.is_verified = True
            user.is_active = True
        else:
            user = User(
                company_id=invitation.company_id,
                role_id=invitation.role_id,
                full_name=full_name,
                email=invitation.email,
                password_hash=AuthService.hash_password(password),
                is_verified=True,
                is_active=True
            )
            db.session.add(user)

        invitation.is_accepted = True
        db.session.commit()

        access_token, refresh_token = AuthService.generate_tokens(user)

        return {
            'message': 'Account created and joined company successfully!',
            'user': {
                'id': user.id,
                'name': user.full_name,
                'email': user.email,
                'role': user.role.name,
                'company_id': user.company_id
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 201

    @classmethod
    def get_team_members(cls, current_user):
        users = User.query.filter_by(company_id=current_user.company_id).all()
        
        # Pending invites sirf Company Admin ko dekhne ki permission hai
        pending_list = []
        if current_user.role.name == 'Company Admin':
            pending_invites = Invitation.query.filter_by(company_id=current_user.company_id, is_accepted=False).all()
            pending_list = [{
                'id': inv.id,
                'email': inv.email,
                'role': inv.role.name,
                'expires_at': inv.expires_at.isoformat(),
                'created_at': inv.created_at.isoformat()
            } for inv in pending_invites]

        members_list = [{
            'id': u.id,
            'full_name': u.full_name,
            'email': u.email,
            'role': u.role.name,
            'is_active': u.is_active,
            'joined_at': u.created_at.isoformat() if u.created_at else None
        } for u in users]

        return {
            'total_members': len(members_list),
            'members': members_list,
            'pending_invitations': pending_list
        }, 200

    @classmethod
    def update_member_role(cls, current_user, member_id, data):
        if current_user.role.name != 'Company Admin':
            return {'error': 'Unauthorized. Only Company Admins can change member roles.'}, 403

        if current_user.id == member_id:
            return {'error': 'Cannot change your own role.'}, 400

        target_user = User.query.filter_by(id=member_id, company_id=current_user.company_id).first()
        if not target_user:
            return {'error': 'Team member not found in your company.'}, 404

        role_name = data.get('role_name', '').strip()
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return {'error': f'Role {role_name} not found.'}, 400

        target_user.role_id = role.id
        db.session.commit()

        return {'message': f"Updated {target_user.full_name}'s role to {role.name}."}, 200