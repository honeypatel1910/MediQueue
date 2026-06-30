from flask import render_template
from flask_login import login_required

from app.admin import admin_bp
from app.decorators import role_required
from app.models import AuditLog, PatientProfile, Role, StaffProfile, User


@admin_bp.route("/dashboard")
@login_required
@role_required("Practice Admin")
def dashboard():
    total_users = User.query.count()
    total_patients = PatientProfile.query.count()
    total_staff = StaffProfile.query.count()
    active_users = User.query.filter_by(active=True).count()
    roles = Role.query.order_by(Role.name.asc()).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_patients=total_patients,
        total_staff=total_staff,
        active_users=active_users,
        roles=roles,
        recent_users=recent_users,
        recent_logs=recent_logs,
    )


@admin_bp.route("/audit-logs")
@login_required
@role_required("Practice Admin")
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return render_template("admin/audit_logs.html", logs=logs)
