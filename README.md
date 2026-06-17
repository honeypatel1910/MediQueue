# MediQueue

MediQueue is a web-based GP appointment and prescription management system being developed as an MSc project.

## Current milestone

This commit combines the database seeding milestone with the first authentication milestone.

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
- Database CLI commands
- Seeded demo users for Patient, Doctor, Nurse and Practice Admin
- Login page
- Logout flow
- Patient registration page
- Simple signed-in account page
- Role protection decorator for future modules

Not included yet:

- Patient/staff profile detail pages
- Role-specific dashboards
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

Reset and seed the local database:

```bash
flask --app run.py reset-db --yes
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

## Demo accounts

After running `flask --app run.py reset-db --yes`, use these accounts:

| Role | Email | Password |
|---|---|---|
| Practice Admin | admin@mediqueue.health | AdminPass123! |
| Doctor | doctor@mediqueue.health | DoctorPass123! |
| Nurse | nurse@mediqueue.health | NursePass123! |
| Patient | patient@mediqueue.health | PatientPass123! |

You can verify seeded accounts with:

```bash
flask --app run.py check-logins
```

## Expected behaviour in this milestone

The app should run and allow users to:

- Open the landing page
- Check the `/health` endpoint
- Create/reset the local database
- Seed demo users
- Log in with demo accounts
- Register a new patient account
- Log out
- View a simple signed-in account page

The website will still look simple because dashboards and feature modules come in later milestones.

## Next milestone

The next commit will add patient profile and patient dashboard backend functionality.
