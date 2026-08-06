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
- Email notification copies for appointment and prescription alerts
- Appointment calendar export with iCalendar (.ics) downloads
- Appointment confirmation emails with .ics calendar attachments
- Audit logging
- CSV report exports for appointments and prescriptions
- JSON API foundation for React authentication
- Email OTP verification for new patient registration

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


## Email OTP verification setup

New patient registrations now require email OTP verification before login. Demo accounts are intentionally kept as seeded test accounts and are treated as already verified so assessment/demo logins continue to work:

```text
admin@mediqueue.health
doctor@mediqueue.health
nurse@mediqueue.health
patient@mediqueue.health
```

Use a real email address only when testing new patient registration. Configure SMTP values in your local `.env` file. Do not commit real SMTP credentials.

```text
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_app_password
MAIL_DEFAULT_SENDER=MediQueue <your_email@example.com>
MAIL_SUPPRESS_SEND=false
EMAIL_OTP_EXPIRY_MINUTES=10
```

For safe testing, Mailtrap is recommended. If `MAIL_SUPPRESS_SEND=true`, the app still creates the OTP record but does not send a real email.

Because this chunk adds a new database table, run this once after applying the chunk:

```bash
flask --app run.py init-db
```

If you are using disposable local test data and want a clean state, you can instead run:

```bash
flask --app run.py reset-db --yes
```

## Email notification setup

MediQueue now sends email copies for the same important alerts that are created as in-app notifications. This includes appointment booking, extra appointment approval requests, appointment approval/rejection, cancellations, prescription updates, prescription payment, and prescription collection updates.

Keep these settings in your local `.env` file:

```text
MAIL_SEND_NOTIFICATIONS=true
MAIL_REDIRECT_ALL_TO=
```

For a live demo with seeded users such as `doctor@mediqueue.health`, set `MAIL_REDIRECT_ALL_TO` to one real inbox. The app will send all outgoing emails to that inbox while showing the original recipient in the email subject/body. This avoids relying on placeholder demo email addresses.

```text
MAIL_REDIRECT_ALL_TO=your_email@example.com
```

If SMTP is unavailable, email sending is safely skipped and the in-app notification still works.


## Appointment calendar export

Confirmed appointments can be exported as iCalendar `.ics` files. Patients can download a calendar invite from Appointment History, while doctors and nurses can export their upcoming confirmed schedule from My Schedule. Pending approval, rejected, cancelled, missed, and completed appointments are not exported as active calendar events.

Appointment confirmation emails also include an `.ics` attachment for booked appointments. When an extra appointment request is approved, the patient approval email includes the calendar invite attachment as well.

The export is file-based, so it works with Google Calendar, Outlook, Apple Calendar, and most mobile calendar apps without requiring Google OAuth permissions.

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

## Secure forgot password flow

MediQueue includes a secure password reset workflow using the same email OTP infrastructure as registration verification.

Flow:

```text
User clicks Forgot password
User enters registered email
System sends a 6-digit password reset OTP
User verifies OTP
User enters new password and retypes the new password
System updates the stored password hash
User signs in with the new password
```

The application validates password confirmation in both React and Flask/API routes. Password reset OTP values are never stored as plain text; they are hashed in the `email_verifications` table with purpose `password_reset`. Once the password has been reset, the OTP record is marked as used so the same OTP cannot be reused.

The reset email uses the same SMTP configuration as registration OTP emails:

```text
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_app_password
EMAIL_OTP_EXPIRY_MINUTES=10
```
