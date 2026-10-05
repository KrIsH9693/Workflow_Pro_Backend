import smtplib
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:

    @staticmethod
    def generate_otp() -> str:
        """Generates a secure 6-digit OTP string."""
        return str(random.randint(100000, 999999))

    @staticmethod
    def _send_email(to_email: str, subject: str, html_content: str):
        mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.getenv('MAIL_PORT', 587))
        mail_user = os.getenv('MAIL_USERNAME')
        mail_pass = os.getenv('MAIL_PASSWORD')
        sender = os.getenv('MAIL_DEFAULT_SENDER', mail_user)

        if not mail_user or not mail_pass:
            print(f"\n[DEV FALLBACK] SMTP not configured. Email to {to_email} with subject '{subject}' not sent via network.")
            return True

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"WorkFlow Pro <{sender}>"
            msg['To'] = to_email

            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(mail_server, mail_port) as server:
                server.starttls()
                server.login(mail_user, mail_pass)
                server.sendmail(sender, to_email, msg.as_string())

            print(f"[SMTP SUCCESS] Email delivered to {to_email}")
            return True
        except Exception as e:
            print(f"[SMTP ERROR] Failed to send email to {to_email}: {str(e)}")
            return False

    @classmethod
    def send_otp_email(cls, to_email: str, otp: str, user_name: str = "User", purpose: str = "Account Verification"):
        subject = f"WorkFlow Pro - Your OTP for {purpose} is {otp}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h2 style="color: #2563eb; text-align: center; margin-bottom: 20px;">WorkFlow Pro</h2>
            <p>Hi <b>{user_name}</b>,</p>
            <p>Use the OTP code below for <b>{purpose}</b>:</p>
            <div style="text-align: center; margin: 30px 0;">
                <span style="font-size: 30px; font-weight: bold; letter-spacing: 5px; color: #1e293b; background: #f8fafc; padding: 12px 24px; border-radius: 8px; border: 2px dashed #cbd5e1; display: inline-block;">{otp}</span>
            </div>
            <p style="color: #64748b; font-size: 13px;">This OTP is valid for 15 minutes. If you did not request this, please ignore this email.</p>
        </div>
        """
        return cls._send_email(to_email, subject, html_content)

    @classmethod
    def send_invite_email(cls, to_email: str, invite_token: str, company_name: str, invited_by_name: str, role_name: str):
        subject = f"You've been invited to join {company_name} on WorkFlow Pro"
        accept_url = f"http://localhost:3000/accept-invite?token={invite_token}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 520px; margin: auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #2563eb; margin: 0;">WorkFlow Pro</h2>
                <p style="color: #64748b; font-size: 14px; margin-top: 5px;">Enterprise Workflow & Task Management</p>
            </div>
            <p>Hello,</p>
            <p><b>{invited_by_name}</b> has invited you to join <b>{company_name}</b> as a <b>{role_name}</b>.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{accept_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 28px; font-size: 15px; font-weight: bold; text-decoration: none; border-radius: 6px; display: inline-block;">Accept Invitation & Join Team</a>
            </div>
            <p style="color: #64748b; font-size: 13px;">Or copy and paste this link in your browser:</p>
            <p style="word-break: break-all; font-size: 12px; color: #2563eb; background: #f1f5f9; padding: 10px; border-radius: 6px;">{accept_url}</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <p style="color: #94a3b8; font-size: 12px; text-align: center;">This invitation link will expire in 24 hours.</p>
        </div>
        """
        return cls._send_email(to_email, subject, html_content)