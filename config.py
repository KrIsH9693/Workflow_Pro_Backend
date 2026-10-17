import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'workflow-pro-secret')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-workflow-secret')

    # Read Supabase PostgreSQL URI from .env
    raw_db_url = os.getenv('DATABASE_URL', 'sqlite:///workflow.db')

    # Fix for SQLAlchemy: Supabase sometimes uses "postgres://", but SQLAlchemy requires "postgresql://"
    if raw_db_url and raw_db_url.startswith('postgres://'):
        raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail / SMTP Configuration (SSL / Port 465)

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))

    # Safe Boolean Check (TLS vs SSL conflict na ho)
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False').strip().lower() in ('yes', 'true', '1')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'True').strip().lower() in ('yes', 'true', '1')

    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # Agar MAIL_DEFAULT_SENDER set nahi hoga toh automatic MAIL_USERNAME use karega
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))