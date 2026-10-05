# WorkFlow Pro — Backend API & Real-Time Engine

WorkFlow Pro is a multi-tenant enterprise workflow and collaboration platform backend built with **Flask**, **PostgreSQL (Supabase)**, **SQLAlchemy**, and **Flask-SocketIO**.

---

## Tech Stack & Architecture

- **Runtime & Framework:** Python 3.10+, Flask
- **Database & ORM:** PostgreSQL (via Supabase), SQLAlchemy
- **Authentication:** JWT (HMAC-SHA256, 32+ byte secret) + OTP-based verification
- **Password Hashing:** Bcrypt
- **Real-Time Layer:** Flask-SocketIO (WebSockets / Event-Driven)
- **Role-Based Access Control (RBAC):** Super Admin, Company Admin, Project Manager, Employee, Team Member, Client, Viewer

---

## Directory Structure

```text
backend/
├── main.py              # Application factory, CORS, exception handlers & entrypoint
├── config.py            # Environment configurations & database connection strings
├── extensions.py        # SQLAlchemy and SocketIO instances
├── models/              # Database models (User, Company, Role, Invitation, etc.)
├── routes/              # Modular blueprints (auth, team, workspaces, projects, etc.)
├── services/            # Core business logic (AuthService, TeamService, etc.)
├── sockets/             # Real-time WebSocket event listeners & broadcasters
├── utils/               # Helper utilities (email dispatchers, formatters)
├── requirements.txt     # Python package dependencies
├── .env                 # Environment secrets (ignored by git)
└── .gitignore           # Git ignore policy

git clone <your-repo-url>
cd workflow-pro/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Environment Variable
# Flask Application Environment
FLASK_ENV=development
SECRET_KEY=workflow-pro-super-secure-production-jwt-key-2026-xyz
JWT_SECRET_KEY=workflow-pro-super-secure-production-jwt-key-2026-xyz

# Supabase PostgreSQL Connection String (URL-encode special characters in password, e.g., @ -> %40)
DATABASE_URL=postgresql://postgres:<PASSWORD>@<SUPABASE_HOST>:5432/postgres

# Frontend URL (For Invitation & Verification Redirects)
FRONTEND_URL=http://localhost:5173

# SMTP Email Configuration (Optional for dev fallback)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-app-password

# Local Development Server
python main.py
API Base URL: http://127.0.0.1:5000
WebSockets: ws://127.0.0.1:5000/socket.io

