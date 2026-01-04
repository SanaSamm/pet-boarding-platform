from db import db
from sqlalchemy import JSON   # ✅ ADD THIS
class BoardingServiceModel(db.Model):
    __tablename__ = "boarding_services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    price_per_day = db.Column(db.Float)
    capacity = db.Column(db.Integer)
    type = db.Column(db.String(50), nullable=False)

    # ✅ JSON column
    services_provided = db.Column(db.JSON, nullable=True)

    # Exact geocoded location (optional)
    geocoded_name = db.Column(db.String(255), nullable=True)
    geocoded_short = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # Soft-delete columns
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    provider_id = db.Column(
        db.Integer,
        db.ForeignKey("providers.id"),
        nullable=False
    )

    provider = db.relationship("ProviderModel", back_populates="services")

    reservations = db.relationship(
        "ReservationModel",
        back_populates="service",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
