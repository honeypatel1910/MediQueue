# MediQueue

MediQueue is a secure web-based GP appointment and prescription management system built with Flask.

## Current functionality

- Flask application factory structure
- Local environment configuration
- PostgreSQL-ready SQLAlchemy configuration with SQLite fallback
- User and role models
- Seeded demo accounts
- Login, logout and patient registration
- Patient profile and dashboard
- Doctor and nurse staff profiles
- Practice admin dashboard
- Admin user management
- Admin appointment and prescription management
- Staff availability management
- Automatic appointment slot generation
- Staff availability editing and slot regeneration
- Patient appointment booking
- Appointment history and cancellation
- Staff schedule and appointment status updates
- Patient prescription request workflow
- Doctor prescription review workflow
- Simulated prescription payment flow
- In-app notifications
- Audit logging

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app run.py reset-db --yes
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## PostgreSQL configuration

Create a `.env` file locally and add your PostgreSQL connection string:

```text
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/mediqueue
SECRET_KEY=change-this-secret-key
```

If `DATABASE_URL` is not set, the app falls back to SQLite for local development.

## Demo accounts

```text
Practice Admin: admin@mediqueue.health / AdminPass123!
Doctor: doctor@mediqueue.health / DoctorPass123!
Nurse: nurse@mediqueue.health / NursePass123!
Patient: patient@mediqueue.health / PatientPass123!
```

## Useful commands

```bash
flask --app run.py reset-db --yes
flask --app run.py seed-data
flask --app run.py check-logins
```
