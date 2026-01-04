from db import db
from datetime import datetime


class ReviewModel(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)

    # legacy owner reference (may be NULL for provider reviewers)
    owner_id = db.Column(db.Integer, db.ForeignKey("owners.id"), nullable=True)

    # new generic reviewer info
    reviewer_role = db.Column(db.String(20), nullable=True)
    reviewer_id = db.Column(db.Integer, nullable=True)

    provider_id = db.Column(db.Integer, db.ForeignKey("providers.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("OwnerModel", foreign_keys=[owner_id])
    provider = db.relationship("ProviderModel", back_populates="reviews")
