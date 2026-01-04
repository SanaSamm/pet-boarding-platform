import sys
sys.path.insert(0, r'c:\Users\samma\pet-boarding-platform')
from app import create_app
from db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    conn = db.engine.connect()
    try:
        res = conn.execute(text("PRAGMA table_info('reviews')")).fetchall()
        # PRAGMA rows may be tuples or RowMappings depending on driver; handle both
        cols = []
        for row in res:
            if hasattr(row, '_mapping'):
                cols.append(row._mapping.get('name'))
            elif isinstance(row, dict):
                cols.append(row.get('name'))
            else:
                # tuple layout: cid, name, type, notnull, dflt_value, pk
                cols.append(row[1])
        print('Current review columns:', cols)
        if 'reviewer_role' not in cols:
            print('Adding reviewer_role')
            conn.execute(text("ALTER TABLE reviews ADD COLUMN reviewer_role TEXT"))
        else:
            print('reviewer_role already present')
        if 'reviewer_id' not in cols:
            print('Adding reviewer_id')
            conn.execute(text("ALTER TABLE reviews ADD COLUMN reviewer_id INTEGER"))
        else:
            print('reviewer_id already present')
        # Ensure owner_id is nullable - skip because sqlite doesn't enforce nullability easily
        print('Done')
    finally:
        conn.close()