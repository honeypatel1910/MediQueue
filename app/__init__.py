from flask import Flask, render_template

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

    register_commands(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(prescriptions_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "MediQueue"}

    return app
