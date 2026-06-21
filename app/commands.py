import click
from flask import current_app

from app.extensions import db
from app.models import PatientProfile, ProfessionalRegister, Role, StaffProfile, User


DEFAULT_ROLES = [
    ("Patient", "Patient user who can book appointments and request prescriptions."),
    ("Doctor", "Clinical staff member who can manage appointments and review prescriptions."),
    ("Nurse", "Clinical staff member who can manage availability and appointments."),
    ("Practice Admin", "Administrative user who manages practice-level operations."),
]

DEMO_USERS = [
    {
        "email": "admin@mediqueue.health",
        "password": "AdminPass123!",
        "first_name": "Practice",
        "last_name": "Admin",
        "role": "Practice Admin",
    },
    {
        "email": "doctor@mediqueue.health",
        "password": "DoctorPass123!",
        "first_name": "Aisha",
        "last_name": "Khan",
        "role": "Doctor",
        "job_title": "General Practitioner",
        "department": "Clinical Services",
        "phone_extension": "201",
        "register_name": "GMC",
        "registration_number": "GMC-7654321",
    },
    {
        "email": "nurse@mediqueue.health",
        "password": "NursePass123!",
        "first_name": "Emily",
        "last_name": "Brown",
        "role": "Nurse",
        "job_title": "Practice Nurse",
        "department": "Nursing Team",
        "phone_extension": "204",
        "register_name": "NMC",
        "registration_number": "NMC-2345678",
    },
    {
        "email": "patient@mediqueue.health",
        "password": "PatientPass123!",
        "first_name": "Sam",
        "last_name": "Taylor",
        "role": "Patient",
        "phone": "07123 456789",
        "address": "12 Riverside Road, Leicester",
    },
]


def seed_roles() -> None:
    """Create default application roles if they do not exist."""
    for name, description in DEFAULT_ROLES:
        role = Role.query.filter_by(name=name).first()
        if role is None:
            db.session.add(Role(name=name, description=description))
    db.session.commit()


def _ensure_patient_profile(user: User, item: dict) -> None:
    """Create a patient profile for patient demo accounts."""
    if not user.has_role("Patient"):
        return

    if user.patient_profile is None:
        user.patient_profile = PatientProfile(
            phone=item.get("phone"),
            address=item.get("address"),
            patient_reference=f"MQP-{user.id or 0:05d}",
        )
    else:
        user.patient_profile.phone = user.patient_profile.phone or item.get("phone")
        user.patient_profile.address = user.patient_profile.address or item.get("address")


def _ensure_staff_profile(user: User, item: dict) -> None:
    """Create staff profile and registration data for doctor and nurse demo accounts."""
    if not user.has_role("Doctor", "Nurse"):
        return

    if user.staff_profile is None:
        user.staff_profile = StaffProfile(
            job_title=item.get("job_title", user.role.name),
            department=item.get("department"),
            phone_extension=item.get("phone_extension"),
        )
        db.session.flush()
    else:
        user.staff_profile.job_title = user.staff_profile.job_title or item.get("job_title", user.role.name)
        user.staff_profile.department = user.staff_profile.department or item.get("department")
        user.staff_profile.phone_extension = user.staff_profile.phone_extension or item.get("phone_extension")

    if user.staff_profile.professional_register is None:
        user.staff_profile.professional_register = ProfessionalRegister(
            register_name=item.get("register_name", "Clinical Register"),
            registration_number=item.get("registration_number", "Pending"),
            verified=True,
        )


def seed_demo_users() -> None:
    """Create demo accounts and role-specific profile data if they do not exist."""
    seed_roles()
    roles = {role.name: role for role in Role.query.all()}

    for item in DEMO_USERS:
        user = User.query.filter_by(email=item["email"]).first()
        if user is None:
            user = User(
                email=item["email"],
                first_name=item["first_name"],
                last_name=item["last_name"],
                role=roles[item["role"]],
                active=True,
            )
            user.set_password(item["password"])
            db.session.add(user)
            db.session.flush()

        _ensure_patient_profile(user, item)
        _ensure_staff_profile(user, item)

    db.session.commit()

    for user in User.query.join(Role).filter(Role.name == "Patient").all():
        if user.patient_profile and not user.patient_profile.patient_reference:
            user.patient_profile.patient_reference = f"MQP-{user.id:05d}"
    db.session.commit()


def register_commands(app):
    """Register custom Flask CLI commands."""

    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-data")
    def seed_data_command():
        """Seed roles, demo users and profile data."""
        db.create_all()
        seed_demo_users()
        click.echo("Seeded roles, demo users and profile data.")
        click.echo("Demo accounts:")
        for item in DEMO_USERS:
            click.echo(f"- {item['email']} / {item['password']} ({item['role']})")

    @app.cli.command("check-logins")
    def check_logins_command():
        """Display seeded demo account status."""
        for item in DEMO_USERS:
            user = User.query.filter_by(email=item["email"]).first()
            status = "available" if user and user.check_password(item["password"]) else "missing or invalid"
            if user and user.has_role("Patient") and user.patient_profile is None:
                status = f"{status}, patient profile missing"
            if user and user.has_role("Doctor", "Nurse") and user.staff_profile is None:
                status = f"{status}, staff profile missing"
            click.echo(f"{item['email']}: {status}")

    @app.cli.command("reset-db")
    @click.option("--yes", is_flag=True, help="Confirm database reset without an interactive prompt.")
    def reset_db_command(yes):
        """Drop and recreate database tables, then seed demo users."""
        if not yes and not click.confirm("This will delete all local database data. Continue?"):
            click.echo("Cancelled.")
            return

        db.drop_all()
        db.create_all()
        seed_demo_users()
        click.echo("Database reset and demo users seeded.")
