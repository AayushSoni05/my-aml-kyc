"""
Creates every table in Postgres. Run this once after updating models.py.
Run with: python scripts/create_tables.py
"""
from app.database import init_db

init_db()
print("All tables created (or already existed).")