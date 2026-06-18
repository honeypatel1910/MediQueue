# MediQueue

MediQueue is an MSc project prototype for a local GP appointment and prescription management system.

## Overview

The application currently provides a secure Flask foundation with user roles, demo accounts, patient registration, patient login, and patient profile management.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create and seed the local database:

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

## Health endpoint

```text
http://127.0.0.1:5000/health
```

Expected response:

```json
{"service":"MediQueue","status":"ok"}
```

## Demo accounts

After running `flask --app run.py reset-db --yes`, use:

| Role | Email | Password |
|---|---|---|
| Practice Admin | admin@mediqueue.health | AdminPass123! |
| Doctor | doctor@mediqueue.health | DoctorPass123! |
| Nurse | nurse@mediqueue.health | NursePass123! |
| Patient | patient@mediqueue.health | PatientPass123! |

Check seeded accounts:

```bash
flask --app run.py check-logins
```

## Current patient flow

1. A patient can register.
2. A patient profile is created automatically during registration.
3. A patient can log in.
4. A patient is redirected to the patient dashboard.
5. A patient can update phone, date of birth, and address from the profile page.
