"""
Jewelry Store — Application Factory (Vercel-compatible)
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:////tmp/jewelry_store.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    # On Vercel only /tmp is writable; locally use app/static/uploads
    is_vercel = os.environ.get("VERCEL") == "1"
    if is_vercel:
        upload_folder = "/tmp/uploads"
    else:
        upload_folder = os.path.join(app.root_path, "static", "uploads")

    app.config["UPLOAD_FOLDER"] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    # ------------------------------------------------------------------
    # Initialise extensions (no Flask-Migrate — not needed on Vercel)
    # ------------------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
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
    # Create tables and seed defaults
    # ------------------------------------------------------------------
    with app.app_context():
        try:
            db.create_all()
            _seed_defaults()
        except Exception as e:
            app.logger.warning(f"DB init warning: {e}")

    return app


def _seed_defaults():
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
        try:
            if not SiteSettings.query.filter_by(key=key).first():
                db.session.add(SiteSettings(key=key, value=value))
        except Exception:
            pass

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
