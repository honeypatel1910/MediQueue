from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Require the logged-in user to have one of the supplied role names."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            if not current_user.has_role(*roles):
                abort(403)

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
