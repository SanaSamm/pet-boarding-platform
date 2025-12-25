"""Database initialization module.

This file defines the SQLAlchemy database instance that is used across
the application. Import `db` from this module in your models to
initialize table mappings and perform CRUD operations.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy instance.  Note that the application
# configuration for the database URI must be set in app.py before
# calling `db.init_app(app)`.
db = SQLAlchemy()