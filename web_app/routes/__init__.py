"""Route blueprints for the application."""

from flask import Blueprint


def register_blueprints(app):
    """Register all blueprints with the application."""
    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .tasks import tasks_bp
    from .forms import forms_bp
    from .attendance import attendance_bp
    from .api import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(forms_bp, url_prefix="/forms")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(api_bp, url_prefix="/api")
