"""Reservations blueprint.

Owners create and manage reservations through this blueprint.  The
endpoints allow creating a reservation for one of the owner's pets,
listing all reservations belonging to the owner, and cancelling a
reservation.  Providers can list reservations by service using the
services blueprint.
"""

from datetime import datetime

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from db import db
from models.reservation import ReservationModel
from models.pet import PetModel
from models.service import BoardingServiceModel
from models.owner import OwnerModel
from schemas.reservation import ReservationSchema


blp = Blueprint(
    "Reservations", __name__, description="Operations on reservations (owner-only)"
)


@blp.route("/reservations")
class ReservationsList(MethodView):
    """Create and list reservations for the current owner."""

    @jwt_required()
    @blp.response(200, ReservationSchema(many=True))
    def get(self):
        identity = get_jwt_identity()
        if identity.get("role") != "owner":
            abort(403, message="Only owners can view their reservations.")

        owner = OwnerModel.query.get_or_404(identity["id"])
        # Gather reservations across all owner's pets
        reservations = []
        for pet in owner.pets:
            reservations.extend(pet.reservations.all())
        return reservations

    @jwt_required()
    @blp.arguments(ReservationSchema)
    @blp.response(201, ReservationSchema)
    def post(self, reservation_data):
        identity = get_jwt_identity()
        if identity.get("role") != "owner":
            abort(403, message="Only owners can create reservations.")

        # Validate pet ownership
        pet = PetModel.query.get_or_404(reservation_data["pet_id"])
        if pet.owner_id != identity["id"]:
            abort(403, message="You can only reserve services for your own pets.")

        # Validate service existence
        service = BoardingServiceModel.query.get_or_404(reservation_data["service_id"])

        # Parse and validate dates
        if reservation_data["start_date"] > reservation_data["end_date"]:
            abort(400, message="start_date must be on or before end_date.")

        # Optional: enforce capacity constraints
        if service.capacity is not None:
            overlapping = ReservationModel.query.filter(
                ReservationModel.service_id == service.id,
                ReservationModel.start_date <= reservation_data["end_date"],
                ReservationModel.end_date >= reservation_data["start_date"],
            ).count()
            if overlapping >= service.capacity:
                abort(409, message="Service is fully booked for the selected dates.")

        reservation = ReservationModel(
            start_date=reservation_data["start_date"],
            end_date=reservation_data["end_date"],
            pet_id=pet.id,
            service_id=service.id,
        )
        db.session.add(reservation)
        db.session.commit()
        return reservation


@blp.route("/reservations/<int:reservation_id>")
class ReservationResource(MethodView):
    """Cancel a specific reservation (owner-only)."""

    @jwt_required()
    def delete(self, reservation_id):
        identity = get_jwt_identity()
        if identity.get("role") != "owner":
            abort(403, message="Only owners can cancel reservations.")

        reservation = ReservationModel.query.get_or_404(reservation_id)
        # Ensure the reservation belongs to one of the owner's pets
        pet = PetModel.query.get(reservation.pet_id)
        if pet.owner_id != identity["id"]:
            abort(403, message="You do not have permission to cancel this reservation.")

        db.session.delete(reservation)
        db.session.commit()
        return {"message": "Reservation cancelled."}