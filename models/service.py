"""SQLAlchemy model for the Boarding Service entity.

Boarding services represent physical locations or hosts where pets
can stay.  Each service is owned by a provider and may have multiple
reservations.  Some fields (price_per_day, capacity) are nullable
because not all services provide fixed pricing or capacity.
"""

from db import db


class BoardingServiceModel(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(80), nullable=False)
    price_per_day = db.Column(db.Float, nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    type = db.Column(db.String(30), nullable=False)

    # Link to provider who owns this service
    provider_id = db.Column(db.Integer, db.ForeignKey("providers.id"), nullable=False)

    provider = db.relationship("ProviderModel", back_populates="services")

    # Relationship: one service can host many reservations
    reservations = db.relationship(
        "ReservationModel", back_populates="service", cascade="all, delete",
        lazy="dynamic"
    )