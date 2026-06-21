# MediQueue

MediQueue is a secure web-based GP appointment and prescription management system developed with Flask.

## Current functionality

- Flask application factory structure
- Environment-based configuration
- SQLAlchemy database setup
- User and role models
- Patient profile model
- Staff profile and professional registration models
- Seeded demo users for patient, doctor, nurse and practice admin roles
- Login, logout and patient registration
- Role-based routing
- Patient dashboard and profile management
- Doctor and nurse staff dashboard
- Practice admin dashboard overview

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

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Practice Admin | admin@mediqueue.health | AdminPass123! |
| Doctor | doctor@mediqueue.health | DoctorPass123! |
| Nurse | nurse@mediqueue.health | NursePass123! |
| Patient | patient@mediqueue.health | PatientPass123! |

## Useful commands

```bash
flask --app run.py reset-db --yes
flask --app run.py seed-data
flask --app run.py check-logins
```
