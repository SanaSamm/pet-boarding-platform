"""SQLAlchemy model for the Reservation entity.

Reservations link pets to boarding services for a specified date
range.  A reservation belongs to one pet and one service.
"""

from db import db


class ReservationModel(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)

    # Relationships back to pet and service
    pet = db.relationship("PetModel", back_populates="reservations")
    service = db.relationship("BoardingServiceModel", back_populates="reservations")