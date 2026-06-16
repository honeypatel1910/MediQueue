# MediQueue

MediQueue is a web-based GP appointment and prescription management system being developed as an MSc project.

## Current milestone

This commit adds the first database foundation on top of the Flask skeleton.

Included so far:

- Flask application factory
- Environment-based configuration
- SQLAlchemy database extension setup
- Flask-Migrate setup
- Flask-Login setup
- CSRF protection setup
- Base template and simple landing page
- Health endpoint at `/health`
- `Role` database model
- `User` database model
- Password hashing and password checking helpers
- Flask-Login user loader

Not included yet:

- Seed users
- Login and registration pages
- Patient/staff profiles
- Appointment workflows
- Prescription workflows
- React frontend
- Tests

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

## Optional database model check

This milestone adds models only. It does not seed users yet. To verify that the database tables can be created locally, run:

```bash
python -c "from app import create_app; from app.extensions import db; from app.models import Role, User; app=create_app(); app.app_context().push(); db.create_all(); print('Created:', Role.__tablename__, User.__tablename__)"
```

This will create a local SQLite database file such as `mediqueue.db`. It is ignored by Git and should not be committed.

## Next milestone

The next commit will add database reset/seed commands and demo users for Patient, Doctor, Nurse and Practice Admin roles.
