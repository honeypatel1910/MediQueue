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
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Notification.created_at.desc()",
    )
    audit_logs = db.relationship(
        "AuditLog",
        back_populates="user",
        order_by="AuditLog.created_at.desc()",
    )
    email_verifications = db.relationship(
        "EmailVerification",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="EmailVerification.created_at.desc()",
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



class EmailVerification(db.Model):
    """Email OTP verification record for patient registration."""

    __tablename__ = "email_verifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    purpose = db.Column(db.String(50), default="registration", nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default="Pending", nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="email_verifications")

    def set_otp(self, otp_code):
        self.otp_hash = generate_password_hash(otp_code)

    def check_otp(self, otp_code):
        return check_password_hash(self.otp_hash, otp_code)

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<EmailVerification {self.email} {self.status}>"


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
    appointments = db.relationship(
        "Appointment",
        back_populates="patient_profile",
        cascade="all, delete-orphan",
        order_by="Appointment.created_at.desc()",
    )
    prescriptions = db.relationship(
        "Prescription",
        back_populates="patient_profile",
        cascade="all, delete-orphan",
        order_by="Prescription.created_at.desc()",
    )

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
    availability_blocks = db.relationship(
        "AvailabilityBlock",
        back_populates="staff_profile",
        cascade="all, delete-orphan",
        order_by="AvailabilityBlock.available_date.asc()",
    )
    appointments = db.relationship(
        "Appointment",
        back_populates="staff_profile",
        cascade="all, delete-orphan",
        order_by="Appointment.created_at.desc()",
    )
    reviewed_prescriptions = db.relationship(
        "Prescription",
        back_populates="reviewed_by_staff",
        foreign_keys="Prescription.reviewed_by_staff_profile_id",
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


class AvailabilityBlock(db.Model):
    """A clinical staff availability window used to generate appointment slots."""

    __tablename__ = "availability_blocks"

    id = db.Column(db.Integer, primary_key=True)
    staff_profile_id = db.Column(db.Integer, db.ForeignKey("staff_profiles.id"), nullable=False, index=True)
    available_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration_minutes = db.Column(db.Integer, default=20, nullable=False)
    location = db.Column(db.String(120), default="GP Practice", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    staff_profile = db.relationship("StaffProfile", back_populates="availability_blocks")
    slots = db.relationship(
        "AppointmentSlot",
        back_populates="availability_block",
        cascade="all, delete-orphan",
        order_by="AppointmentSlot.start_at.asc()",
    )

    @property
    def slot_count(self):
        return len(self.slots or [])

    def __repr__(self):
        return f"<AvailabilityBlock {self.available_date} {self.start_time}-{self.end_time}>"


class AppointmentSlot(db.Model):
    """A bookable appointment slot generated from staff availability."""

    __tablename__ = "appointment_slots"

    id = db.Column(db.Integer, primary_key=True)
    availability_block_id = db.Column(db.Integer, db.ForeignKey("availability_blocks.id"), nullable=False, index=True)
    start_at = db.Column(db.DateTime, nullable=False, index=True)
    end_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), default="Available", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    availability_block = db.relationship("AvailabilityBlock", back_populates="slots")
    appointments = db.relationship(
        "Appointment",
        back_populates="slot",
        cascade="all, delete-orphan",
    )

    @property
    def staff_profile(self):
        return self.availability_block.staff_profile if self.availability_block else None

    def __repr__(self):
        return f"<AppointmentSlot {self.start_at} {self.status}>"


class Appointment(db.Model):
    """A patient appointment booked against a generated staff slot."""

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_profile_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    staff_profile_id = db.Column(db.Integer, db.ForeignKey("staff_profiles.id"), nullable=False, index=True)
    appointment_slot_id = db.Column(db.Integer, db.ForeignKey("appointment_slots.id"), nullable=False, index=True)
    status = db.Column(db.String(30), default="Booked", nullable=False, index=True)
    reason = db.Column(db.String(255))
    internal_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient_profile = db.relationship("PatientProfile", back_populates="appointments")
    staff_profile = db.relationship("StaffProfile", back_populates="appointments")
    slot = db.relationship("AppointmentSlot", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment {self.id} {self.status}>"

class Prescription(db.Model):
    """A patient prescription request reviewed by clinical staff."""

    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    patient_profile_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    reviewed_by_staff_profile_id = db.Column(db.Integer, db.ForeignKey("staff_profiles.id"), nullable=True)
    medicine_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.String(80), nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.String(50), default="Requested", nullable=False, index=True)
    payment_status = db.Column(db.String(30), default="Not Required", nullable=False, index=True)
    amount_due = db.Column(db.Float, default=0.0, nullable=False)
    payment_method = db.Column(db.String(40))
    payment_reference = db.Column(db.String(80), unique=True, index=True)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime)

    patient_profile = db.relationship("PatientProfile", back_populates="prescriptions")
    reviewed_by_staff = db.relationship(
        "StaffProfile",
        back_populates="reviewed_prescriptions",
        foreign_keys=[reviewed_by_staff_profile_id],
    )

    @property
    def payment_label(self):
        if self.payment_status == "Paid":
            return "Paid"
        if self.payment_status == "Pending":
            return "Payment Pending"
        return "Not Required"

    def __repr__(self):
        return f"<Prescription {self.id} {self.status}>"

class Notification(db.Model):
    """In-app notification shown to a specific MediQueue user."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} {self.title}>"



class AuditLog(db.Model):
    """Security and activity record for important MediQueue actions."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(120), nullable=False)
    entity_type = db.Column(db.String(80))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.String(500))
    ip_address = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type} {self.entity_id}>"
