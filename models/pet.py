"""SQLAlchemy model for the Pet entity.

Pets belong to owners and can have multiple reservations over time.
This model stores basic identifying information about each pet.
"""

from db import db


class PetModel(db.Model):
    __tablename__ = "pets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("owners.id"), nullable=False)

    # Relationship back to owner
    owner = db.relationship("OwnerModel", back_populates="pets")

    # Relationship: one pet can have many reservations
    reservations = db.relationship(
        "ReservationModel", back_populates="pet", cascade="all, delete",
        lazy="dynamic"
    )