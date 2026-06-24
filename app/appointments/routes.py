from datetime import date, datetime, time

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.decorators import role_required
from app.extensions import db
from app.models import Appointment, AppointmentSlot, StaffProfile
from app.services import book_appointment, cancel_appointment
from app.appointments import appointments_bp


def _appointment_redirect():
    if current_user.has_role("Patient"):
        return redirect(url_for("patients.appointments"))
    if current_user.has_role("Doctor", "Nurse"):
        return redirect(url_for("staff.schedule"))
    if current_user.has_role("Practice Admin"):
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("index"))


@appointments_bp.route("/available")
@login_required
@role_required("Patient")
def available_slots():
    """Show future available appointment slots to patients."""
    selected_date = request.args.get("date")
    selected_staff_id = request.args.get("staff_id", type=int)

    query = AppointmentSlot.query.filter(AppointmentSlot.status == "Available")
    query = query.filter(AppointmentSlot.start_at >= datetime.combine(date.today(), time.min))

    if selected_date:
        try:
            filter_date = date.fromisoformat(selected_date)
            query = query.filter(
                AppointmentSlot.start_at >= datetime.combine(filter_date, time.min),
                AppointmentSlot.start_at <= datetime.combine(filter_date, time.max),
            )
        except ValueError:
            flash("Please choose a valid appointment date.", "warning")

    if selected_staff_id:
        query = query.join(AppointmentSlot.availability_block).filter_by(staff_profile_id=selected_staff_id)

    slots = query.order_by(AppointmentSlot.start_at.asc()).limit(100).all()
    staff_list = StaffProfile.query.order_by(StaffProfile.job_title.asc()).all()

    return render_template(
        "appointments/available.html",
        slots=slots,
        staff_list=staff_list,
        selected_date=selected_date,
        selected_staff_id=selected_staff_id,
    )


@appointments_bp.route("/slots/<int:slot_id>/book", methods=["POST"])
@login_required
@role_required("Patient")
def book(slot_id):
    """Book an available appointment slot for the logged-in patient."""
    reason = request.form.get("reason", "").strip()

    try:
        book_appointment(current_user.patient_profile, slot_id, reason=reason)
        db.session.commit()
        flash("Appointment booked successfully.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
    except IntegrityError:
        db.session.rollback()
        flash("This appointment slot is no longer available. Please select another slot.", "danger")

    return redirect(url_for("appointments.available_slots"))


@appointments_bp.route("/<int:appointment_id>/cancel", methods=["POST"])
@login_required
def cancel(appointment_id):
    """Cancel a booked appointment when the current user is allowed to manage it."""
    appointment = Appointment.query.get_or_404(appointment_id)

    allowed = False
    if current_user.has_role("Patient") and appointment.patient_profile.user_id == current_user.id:
        allowed = True
    if current_user.has_role("Doctor", "Nurse") and appointment.staff_profile.user_id == current_user.id:
        allowed = True
    if current_user.has_role("Practice Admin"):
        allowed = True

    if not allowed:
        flash("You do not have permission to cancel this appointment.", "danger")
        return _appointment_redirect()

    try:
        cancel_appointment(appointment)
        db.session.commit()
        flash("Appointment cancelled successfully.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return _appointment_redirect()
