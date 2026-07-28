from datetime import datetime
from uuid import uuid4

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.decorators import role_required
from app.extensions import db
from app.models import PatientProfile, Prescription
from app.prescriptions import prescriptions_bp
from app.prescriptions.forms import PrescriptionPaymentForm, PrescriptionRequestForm, PrescriptionReviewForm
from app.services import log_action, notify_role, notify_user


PRESCRIPTION_STANDARD_FEE = 9.90


def ensure_patient_profile(user):
    """Create a patient profile for patient accounts that do not have one yet."""
    if user.patient_profile is None:
        user.patient_profile = PatientProfile(patient_reference=f"MQP-{user.id:05d}")
        db.session.commit()
    return user.patient_profile


@prescriptions_bp.route("/request", methods=["GET", "POST"])
@login_required
@role_required("Patient")
def request_prescription():
    profile = ensure_patient_profile(current_user)
    form = PrescriptionRequestForm()

    if form.validate_on_submit():
        prescription = Prescription(
            patient_profile_id=profile.id,
            medicine_name=form.medicine_name.data,
            quantity=form.quantity.data,
            reason=form.reason.data,
            status="Requested",
            payment_status="Not Required",
            amount_due=0.0,
        )
        db.session.add(prescription)
        db.session.flush()
        notify_user(
            profile.user_id,
            "Prescription request submitted",
            f"Your prescription request for {prescription.medicine_name} has been submitted and is awaiting doctor review.",
        )
        notify_role(
            "Doctor",
            "New prescription request",
            f"{current_user.full_name} requested {prescription.medicine_name}. Please review the request in MediQueue.",
            exclude_user_ids={current_user.id},
        )
        log_action(
            "Prescription requested",
            "Prescription",
            prescription.id,
            f"Medicine: {prescription.medicine_name}",
        )
        db.session.commit()
        flash("Prescription request submitted successfully.", "success")
        return redirect(url_for("prescriptions.history"))

    return render_template("prescriptions/request.html", form=form)


@prescriptions_bp.route("/history")
@login_required
@role_required("Patient")
def history():
    profile = ensure_patient_profile(current_user)
    prescriptions = (
        Prescription.query.filter_by(patient_profile_id=profile.id)
        .order_by(Prescription.created_at.desc())
        .all()
    )
    return render_template("prescriptions/history.html", prescriptions=prescriptions)


@prescriptions_bp.route("/manage")
@login_required
@role_required("Doctor")
def manage():
    prescriptions = Prescription.query.order_by(Prescription.created_at.desc()).all()
    return render_template("prescriptions/manage.html", prescriptions=prescriptions)


@prescriptions_bp.route("/<int:prescription_id>/review", methods=["GET", "POST"])
@login_required
@role_required("Doctor")
def review(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    form = PrescriptionReviewForm(obj=prescription)

    if form.validate_on_submit():
        new_status = form.status.data
        prescription.status = new_status
        prescription.reviewed_at = datetime.utcnow()

        if current_user.staff_profile:
            prescription.reviewed_by_staff_profile_id = current_user.staff_profile.id

        if new_status == "Approved":
            prescription.payment_status = "Pending"
            prescription.amount_due = PRESCRIPTION_STANDARD_FEE
        elif new_status == "Rejected":
            prescription.payment_status = "Not Required"
            prescription.amount_due = 0.0
        elif new_status in {"Requested", "Under Review"}:
            prescription.payment_status = "Not Required"
            prescription.amount_due = 0.0

        notify_user(
            prescription.patient_profile.user_id,
            "Prescription updated",
            f"Your prescription request for {prescription.medicine_name} is now: {prescription.status}.",
        )
        log_action(
            "Prescription reviewed",
            "Prescription",
            prescription.id,
            f"Status set to {prescription.status}",
        )
        db.session.commit()
        flash("Prescription status updated successfully.", "success")
        return redirect(url_for("prescriptions.manage"))

    return render_template("prescriptions/review.html", form=form, prescription=prescription)


@prescriptions_bp.route("/<int:prescription_id>/pay", methods=["GET", "POST"])
@login_required
@role_required("Patient")
def pay_prescription(prescription_id):
    profile = ensure_patient_profile(current_user)
    prescription = Prescription.query.get_or_404(prescription_id)

    if prescription.patient_profile_id != profile.id:
        flash("You can only pay for your own prescription requests.", "danger")
        return redirect(url_for("prescriptions.history"))

    if prescription.status != "Approved":
        flash("Only approved prescriptions can be paid.", "warning")
        return redirect(url_for("prescriptions.history"))

    if prescription.payment_status == "Paid":
        flash("This prescription has already been paid.", "info")
        return redirect(url_for("prescriptions.history"))

    if prescription.payment_status != "Pending" or not prescription.amount_due:
        flash("There is no payment due for this prescription.", "info")
        return redirect(url_for("prescriptions.history"))

    form = PrescriptionPaymentForm()
    if form.validate_on_submit():
        prescription.payment_status = "Paid"
        prescription.payment_method = form.payment_method.data
        prescription.payment_reference = f"MQPAY-{uuid4().hex[:10].upper()}"
        prescription.paid_at = datetime.utcnow()
        notify_user(
            prescription.patient_profile.user_id,
            "Prescription payment received",
            f"Payment has been received for {prescription.medicine_name}. Reference: {prescription.payment_reference}.",
        )
        log_action(
            "Prescription payment completed",
            "Prescription",
            prescription.id,
            f"Payment reference: {prescription.payment_reference}",
        )
        db.session.commit()
        flash("Prescription payment completed successfully.", "success")
        return redirect(url_for("prescriptions.history"))

    return render_template("prescriptions/pay.html", form=form, prescription=prescription)
