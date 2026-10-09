"""
One-off migration: add card_slug column to resources table.
Run once from your project root: python3 migrate_card_slug.py
"""
import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_PATH", "jag.db")

conn = sqlite3.connect(DB_PATH)
try:
    conn.execute("ALTER TABLE resources ADD COLUMN card_slug TEXT")
    conn.commit()
    print(f"✓ card_slug column added to resources in {DB_PATH}")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print(f"✓ card_slug already exists — nothing to do.")
    else:
        raise
finally:
    conn.close()
