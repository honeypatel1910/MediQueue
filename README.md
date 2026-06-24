# MediQueue

MediQueue is a secure web-based GP appointment and prescription management system built with Flask.

## Current functionality

- Flask application factory structure
- Local environment configuration
- SQLAlchemy database setup
- User and role models
- Seeded demo accounts
- Login, logout and patient registration
- Patient profile and dashboard
- Doctor and nurse staff profiles
- Practice admin dashboard
- Staff availability management
- Automatic appointment slot generation
- Patient appointment booking
- Appointment history and cancellation
- Staff schedule and appointment status updates

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
