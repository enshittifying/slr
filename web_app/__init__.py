"""Flask application factory for the SLR Workflow Management System."""

import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS

from .models import db, User
from .config import get_config


login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        config_name: Configuration name ('development', 'production', 'testing')

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    config = get_config(config_name)
    app.config.from_object(config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app)

    # Configure login manager
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        return User.query.get(user_id)

    # Register blueprints
    from .routes import register_blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):
    """Register error handlers for the application."""

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {"error": "Internal server error"}, 500

    @app.errorhandler(403)
    def forbidden(error):
        return {"error": "Forbidden"}, 403

    @app.errorhandler(401)
    def unauthorized(error):
        return {"error": "Unauthorized"}, 401
