from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Notification
from app.notifications import notifications_bp


@notifications_bp.route("/")
@login_required
def list_notifications():
    notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications/list.html", notifications=notifications)


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    flash("Notification marked as read.", "success")
    return redirect(url_for("notifications.list_notifications"))
