"""SQLAlchemy model for the Owner entity.

An owner represents a pet parent who can register on the platform,
manage multiple pets, and create reservations.  Owners have a one‑to‑
many relationship with `PetModel`.
"""

from db import db


class OwnerModel(db.Model):
    __tablename__ = "owners"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relationship: one owner can have many pets
    pets = db.relationship(
        "PetModel", back_populates="owner", cascade="all, delete",
        lazy="dynamic"
    )