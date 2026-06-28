"""Entry point for production WSGI servers (gunicorn, waitress, etc).

Example:
    pip install gunicorn
    gunicorn wsgi:application --bind 0.0.0.0:8000
"""
import db
from app import application  # noqa: F401  (re-exported for the WSGI server)

db.init_db()
db.seed_demo_data()
