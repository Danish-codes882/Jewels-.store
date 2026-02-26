"""
Jewelry Store — Application Factory
=====================================
Creates and configures the Flask application, registers blueprints,
initialises extensions, and seeds default site settings on first run.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Extension instances (initialised without an app; bound in create_app)
# ---------------------------------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    """Application factory — returns a fully configured Flask app."""

    app = Flask(__name__, instance_relative_config=False)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///jewelry_store.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = int(
        os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)  # 16 MB upload limit
    )
    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.root_path, "static", "uploads"
    )

    # ------------------------------------------------------------------
    # Initialise extensions
    # ------------------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = "admin_bp.login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    # ------------------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------------------
    from app.main import main_bp
    from app.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ------------------------------------------------------------------
    # Create tables and seed default data on first run
    # ------------------------------------------------------------------
    with app.app_context():
        db.create_all()
        _seed_defaults()

    return app


def _seed_defaults():
    """Insert default SiteSettings rows if the table is empty."""
    from app.models import SiteSettings

    defaults = {
        "site_name": "Jewels & Co.",
        "site_tagline": "Timeless elegance, crafted for you.",
        "currency_symbol": "$",
        "logo_image": "",
        "background_image": "",
        "delivery_cost": "5.00",
        "free_delivery_threshold": "50.00",
        "announcement_text": "",
        "contact_email": "contact@jewelsco.com",
        "contact_phone": "",
        "instagram_url": "",
        "facebook_url": "",
    }

    for key, value in defaults.items():
        if not SiteSettings.query.filter_by(key=key).first():
            db.session.add(SiteSettings(key=key, value=value))

    db.session.commit()
