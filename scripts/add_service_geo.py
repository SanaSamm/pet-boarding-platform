"""Small utility to add geography columns to the boarding_services table if they
are missing. Safe to run multiple times.

Usage:
    python scripts/add_service_geo.py

It supports SQLite and Postgres (basic ALTER syntax).
"""
import os
import sqlite3
import sys

DB_URL = os.getenv('DATABASE_URL', 'sqlite:///instance/app.db')

if DB_URL.startswith('sqlite:///'):
    # For sqlite, the file path follows sqlite:///
    db_path = DB_URL.replace('sqlite:///', '')
    if not os.path.exists(db_path):
        print(f"DB file not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check columns
    cur.execute("PRAGMA table_info(boarding_services)")
    cols = [r[1] for r in cur.fetchall()]

    changes = []
    if 'geocoded_name' not in cols:
        cur.execute("ALTER TABLE boarding_services ADD COLUMN geocoded_name TEXT;")
        changes.append('geocoded_name')
    if 'latitude' not in cols:
        cur.execute("ALTER TABLE boarding_services ADD COLUMN latitude FLOAT;")
        changes.append('latitude')
    if 'longitude' not in cols:
        cur.execute("ALTER TABLE boarding_services ADD COLUMN longitude FLOAT;")
        changes.append('longitude')
    if 'geocoded_short' not in cols:
        cur.execute("ALTER TABLE boarding_services ADD COLUMN geocoded_short TEXT;")
        changes.append('geocoded_short')
    if 'is_deleted' not in cols:
        cur.execute("ALTER TABLE boarding_services ADD COLUMN is_deleted INTEGER DEFAULT 0;")
        changes.append('is_deleted')
    if 'deleted_at' not in cols:
        cur.execute("ALTER TABLE boarding_services ADD COLUMN deleted_at DATETIME;")
        changes.append('deleted_at')

    conn.commit()
    conn.close()

    if changes:
        print('Added columns:', ', '.join(changes))
    else:
        print('No changes. Columns already present.')
else:
    print('This script only supports SQLite for now. For other databases, run equivalent ALTER TABLE commands:')
    print('ALTER TABLE boarding_services ADD COLUMN geocoded_name TEXT;')
    print('ALTER TABLE boarding_services ADD COLUMN latitude FLOAT;')
    print('ALTER TABLE boarding_services ADD COLUMN longitude FLOAT;')

