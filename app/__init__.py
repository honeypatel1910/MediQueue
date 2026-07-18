from pathlib import Path

from flask import Flask, render_template, send_from_directory

from app.config import Config
from app.extensions import csrf, db, login_manager, migrate


@login_manager.user_loader
def load_user(user_id):
    """Load the logged-in user from the session for Flask-Login."""
    from app.models import User

    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def create_app(config_class=Config):
    """Create and configure the MediQueue Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from app.commands import register_commands
    from app.auth import bp as auth_bp
    from app.patients import patients_bp
    from app.staff import staff_bp
    from app.admin import admin_bp
    from app.appointments import appointments_bp
    from app.prescriptions import prescriptions_bp
    from app.notifications import notifications_bp
    from app.reports import reports_bp
    from app.api import api_bp

    register_commands(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(prescriptions_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    react_dist = Path(app.root_path).parent / "frontend" / "dist"

    @app.route("/assets/<path:filename>")
    def react_assets(filename):
        """Serve compiled React assets when the frontend has been built."""
        return send_from_directory(react_dist / "assets", filename)

    @app.route("/")
    def index():
        """Serve the React frontend if built; otherwise use the Flask landing page."""
        if (react_dist / "index.html").exists():
            return send_from_directory(react_dist, "index.html")
        return render_template("index.html")

    @app.route("/app")
    @app.route("/app/<path:_path>")
    def react_app(_path=None):
        """Serve the React single-page app for production frontend routes."""
        if (react_dist / "index.html").exists():
            return send_from_directory(react_dist, "index.html")
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "MediQueue"}

    return app
