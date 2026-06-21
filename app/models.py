from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Role(db.Model):
    """Application role such as Patient, Doctor, Nurse or Practice Admin."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    users = db.relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    """Core login account shared by every role in MediQueue."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship("Role", back_populates="users")
    patient_profile = db.relationship(
        "PatientProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    staff_profile = db.relationship(
        "StaffProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def is_active(self):
        """Required by Flask-Login to block inactive accounts."""
        return self.active

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        return self.role is not None and self.role.name in roles

    def __repr__(self):
        return f"<User {self.email}>"


class PatientProfile(db.Model):
    """Patient-specific details linked to a login account."""

    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.String(255))
    patient_reference = db.Column(db.String(50), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="patient_profile")

    def __repr__(self):
        return f"<PatientProfile {self.patient_reference or self.id}>"


class StaffProfile(db.Model):
    """Doctor or nurse details linked to a login account."""

    __tablename__ = "staff_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    job_title = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(120))
    phone_extension = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="staff_profile")
    professional_register = db.relationship(
        "ProfessionalRegister",
        back_populates="staff_profile",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<StaffProfile {self.job_title} {self.user_id}>"


class ProfessionalRegister(db.Model):
    """Professional registration details for clinical staff."""

    __tablename__ = "professional_registers"

    id = db.Column(db.Integer, primary_key=True)
    staff_profile_id = db.Column(db.Integer, db.ForeignKey("staff_profiles.id"), unique=True, nullable=False)
    register_name = db.Column(db.String(50), nullable=False)
    registration_number = db.Column(db.String(80), nullable=False)
    verified = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    staff_profile = db.relationship("StaffProfile", back_populates="professional_register")

    def __repr__(self):
        return f"<ProfessionalRegister {self.register_name} {self.registration_number}>"
