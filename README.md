# MediQueue

MediQueue is a secure web-based GP appointment and prescription management system.

## Current functionality

- Flask backend application structure
- Local database configuration
- Role-based accounts for Patient, Doctor, Nurse and Practice Admin
- Patient registration, login and logout
- Patient profile and dashboard
- Doctor and nurse staff profiles
- Staff availability creation
- Automatic appointment slot generation
- Patient appointment slot browsing and booking
- Practice Admin dashboard overview

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

## Appointment booking flow

1. Log in as doctor or nurse.
2. Open Staff Dashboard.
3. Add availability from the availability page.
4. Log out and log in as the patient.
5. Open Book Appointment.
6. Select and book an available slot.

## Useful commands

```bash
flask --app run.py reset-db --yes
flask --app run.py check-logins
python run.py
```
