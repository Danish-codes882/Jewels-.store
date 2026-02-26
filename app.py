"""
Vercel Entry Point
==================
Vercel's filesystem is read-only except for /tmp.
This patches config so SQLite writes to /tmp, and ensures
SECRET_KEY is always available.
"""

import os

# Force SQLite into /tmp (only writable dir on Vercel)
# If you set DATABASE_URL in Vercel dashboard, that is used instead.
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite:////tmp/jewelry_store.db"

# Ensure SECRET_KEY is always present
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "vercel-temp-secret-change-me"

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
