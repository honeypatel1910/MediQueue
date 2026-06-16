# MediQueue

MediQueue is a web-based GP appointment and prescription management system being developed as an MSc project.

## Current milestone

This commit contains the initial Flask backend structure only.

Included so far:

- Flask application factory
- Environment-based configuration
- SQLAlchemy database extension setup
- Flask-Migrate setup
- Flask-Login setup
- CSRF protection setup
- Base template and simple landing page
- Health endpoint at `/health`

Planned later milestones:

- User and role database models
- Demo seed users
- Authentication and role-based access
- Patient dashboard and profile
- Staff availability and automatic appointment slot generation
- Appointment booking and cancellation
- Prescription request, review and payment workflow
- Notifications, audit logs and reports
- React frontend integration
- Tests and health check script

## Local setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional environment setup:

```bash
copy .env.example .env
```

Run the app:

```bash
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

Check health endpoint:

```text
http://127.0.0.1:5000/health
```
