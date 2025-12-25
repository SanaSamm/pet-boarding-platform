"""SQLAlchemy model for the Provider entity.

A provider represents a business or individual offering pet boarding
services (e.g. pet hotels, hosts, veterinary clinics).  Providers
manage one or more `BoardingServiceModel` records.  Providers can
register and log in separately from owners, allowing them to
maintain their own services and view reservations for those services.
"""

from db import db


class ProviderModel(db.Model):
    __tablename__ = "providers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relationship: one provider can offer many services
    services = db.relationship(
        "BoardingServiceModel", back_populates="provider", cascade="all, delete",
        lazy="dynamic"
    )