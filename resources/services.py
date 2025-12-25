"""Boarding services blueprint.

This blueprint provides endpoints to list and search boarding services
for all users, as well as create, update and delete services for
providers.  It also allows providers to view reservations for their
services and check availability.
"""

from datetime import datetime

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from db import db
from models.service import BoardingServiceModel
from models.provider import ProviderModel
from models.reservation import ReservationModel
from schemas.service import BoardingServiceSchema
from schemas.reservation import ReservationSchema


blp = Blueprint(
    "Services", __name__, description="Operations on boarding services"
)


def _apply_service_filters(query, params):
    """Apply filtering parameters to a services query.

    Supported parameters:
    - location: substring match on location field (case-insensitive)
    - type: exact match on service type
    - max_price: services with price_per_day <= max_price
    """
    location = params.get("location")
    if location:
        query = query.filter(BoardingServiceModel.location.ilike(f"%{location}%"))

    svc_type = params.get("type")
    if svc_type:
        query = query.filter(BoardingServiceModel.type == svc_type)

    max_price = params.get("max_price")
    if max_price is not None:
        try:
            max_price = float(max_price)
            query = query.filter(
                (BoardingServiceModel.price_per_day != None) &
                (BoardingServiceModel.price_per_day <= max_price)
            )
        except ValueError:
            abort(400, message="max_price must be a number")
    return query


@blp.route("/services")
class ServiceList(MethodView):

    @blp.response(200, BoardingServiceSchema(many=True))
    def get(self):
        services = BoardingServiceModel.query.all()

        result = []
        for s in services:
            result.append({
                "id": s.id,
                "name": s.name,
                "location": s.location,
                "lat": s.lat,
                "lng": s.lng,
                "capacity": s.capacity,
                "type": s.type,
                # business flag (later dynamic)
                "available": True if s.capacity and s.capacity > 0 else False
            })

        return result



@blp.route("/services/<int:service_id>")
class ServiceResource(MethodView):
    """Retrieve, update, or delete a specific service."""

    @blp.response(200, BoardingServiceSchema)
    def get(self, service_id):
        service = BoardingServiceModel.query.get_or_404(service_id)
        return service

    @jwt_required()
    @blp.arguments(BoardingServiceSchema)
    @blp.response(200, BoardingServiceSchema)
    def put(self, service_data, service_id):
        identity = get_jwt_identity()
        if identity.get("role") != "provider":
            abort(403, message="Only providers can update services.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.provider_id != identity["id"]:
            abort(403, message="You can only update your own services.")

        service.name = service_data["name"]
        service.location = service_data["location"]
        service.price_per_day = service_data.get("price_per_day")
        service.capacity = service_data.get("capacity")
        service.type = service_data["type"]
        db.session.commit()
        return service

    @jwt_required()
    def delete(self, service_id):
        identity = get_jwt_identity()
        if identity.get("role") != "provider":
            abort(403, message="Only providers can delete services.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.provider_id != identity["id"]:
            abort(403, message="You can only delete your own services.")

        db.session.delete(service)
        db.session.commit()
        return {"message": "Service deleted."}


@blp.route("/services/<int:service_id>/reservations")
class ServiceReservations(MethodView):
    """List reservations for a specific service (provider only)."""

    @jwt_required()
    @blp.response(200, ReservationSchema(many=True))
    def get(self, service_id):
        identity = get_jwt_identity()
        if identity.get("role") != "provider":
            abort(403, message="Only providers can view reservations for their services.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.provider_id != identity["id"]:
            abort(403, message="You can only view reservations for your own services.")

        return service.reservations.all()


@blp.route("/services/<int:service_id>/availability")
class ServiceAvailability(MethodView):
    """Check availability for a service over a date range (public)."""

    @blp.response(200)
    def get(self, service_id):
        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.capacity is None:
            return {
                "available": False,
                "message": "Capacity information not provided for this service."
            }

        # Parse dates from query parameters
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        if not start_date_str or not end_date_str:
            abort(400, message="start_date and end_date query parameters are required (YYYY-MM-DD)")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            abort(400, message="Invalid date format. Use YYYY-MM-DD.")

        # Count existing reservations overlapping the requested range
        overlapping_reservations = ReservationModel.query.filter(
            ReservationModel.service_id == service_id,
            ReservationModel.start_date <= end_date,
            ReservationModel.end_date >= start_date,
        ).count()

        available_count = service.capacity - overlapping_reservations
        return {
            "service_id": service_id,
            "capacity": service.capacity,
            "reserved": overlapping_reservations,
            "available": max(available_count, 0),
        }