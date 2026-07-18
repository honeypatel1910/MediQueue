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
- CSV report exports for appointments and prescriptions
- JSON API foundation for React authentication

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

## API foundation

Initial JSON API endpoints are available for the React frontend:

```text
/api/health
/api/session
/api/login
/api/logout
/api/register
```

These endpoints use the same Flask-Login session as the server-rendered pages.

## React production build through Flask

After the React frontend is built, Flask serves the compiled frontend from:

```text
frontend/dist
```

Use this when testing the integrated application from one address:

```bash
cd frontend
npm install
npm run build
cd ..
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

During development, you can still run React separately with:

```bash
cd frontend
npm run dev
```

The Vite development server proxies `/api` and `/reports` requests to the Flask backend.
