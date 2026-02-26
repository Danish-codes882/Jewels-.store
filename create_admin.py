"""
Create First Admin User
=======================
Run once after setting up the database:

    python create_admin.py

You will be prompted for a username, email, and password.
"""

import getpass
from app import create_app, db
from app.models import Admin


def create_admin():
    app = create_app()
    with app.app_context():
        print("\n── Create Admin User ─────────────────────")

        username = input("Username [admin]: ").strip() or "admin"
        email    = input("Email: ").strip()

        if Admin.query.filter_by(username=username).first():
            print(f"❌  Admin '{username}' already exists.")
            return

        password = getpass.getpass("Password (min 8 chars): ")
        if len(password) < 8:
            print("❌  Password must be at least 8 characters.")
            return

        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("❌  Passwords do not match.")
            return

        admin = Admin(username=username, email=email, is_active=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        print(f"\n✅  Admin '{username}' created successfully!")
        print(f"    Log in at: http://localhost:5000/admin/login\n")


if __name__ == "__main__":
    create_admin()
