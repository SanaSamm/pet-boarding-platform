"""
Boarding services blueprint.

This blueprint provides endpoints to list and search boarding services
for all users, as well as create, update and delete services for
providers. It also allows providers to view reservations for their
services and check availability.
"""

from datetime import datetime
import os
import math
import requests

from flask import request, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from db import db
from models.service import BoardingServiceModel
from models.reservation import ReservationModel
from models.provider import ProviderModel
from schemas.service import BoardingServiceSchema
from schemas.reservation import ReservationSchema


def _haversine_km(lat1, lon1, lat2, lon2):
    """Return distance in kilometers between two lat/lon points."""
    # Convert degrees to radians
    r = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return r * c


blp = Blueprint(
    "Services", __name__, description="Operations on boarding services"
)


@blp.route("/geocode/reverse")
class ReverseGeocode(MethodView):
    """Reverse-geocode coordinates into a friendly address.

    Uses a configured Maps Pro API (set via MAPS_PRO_URL and MAPS_PRO_KEY)
    if available, otherwise falls back to OpenStreetMap Nominatim.
    """

    def get(self):
        lat = request.args.get("lat")
        lng = request.args.get("lng") or request.args.get("lon")
        if not lat or not lng:
            abort(400, message="lat and lng are required")

        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except ValueError:
            abort(400, message="Invalid coordinates")

        maps_url = os.getenv("MAPS_PRO_URL")
        maps_key = os.getenv("MAPS_PRO_KEY")

        if maps_url and maps_key:
            try:
                resp = requests.get(maps_url, params={"lat": lat_f, "lng": lng_f, "key": maps_key}, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                # Expecting { display_name: "..." } or similar
                # Prefer to return both a concise display and the raw/full display if available
                full = data.get("display_name") or data.get("address") or data.get("label") or data.get("formatted") or data.get("name")
                # Attempt to extract locality components if provided by the Maps Pro response
                addr = data.get('address') if isinstance(data.get('address'), dict) else {}
                locality = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality') or addr.get('hamlet')
                suburb = addr.get('suburb') or addr.get('quarter') or addr.get('neighbourhood')
                if suburb and locality:
                    display = f"{suburb}, {locality}"
                elif locality:
                    display = locality
                elif suburb:
                    display = suburb
                else:
                    # Prefer county with postcode when available
                    if addr.get('county') and addr.get('postcode'):
                        display = f"{addr.get('county')} ({addr.get('postcode')})"
                    elif addr.get('county'):
                        display = addr.get('county')
                    elif addr.get('state'):
                        display = addr.get('state')
                    elif addr.get('postcode'):
                        display = addr.get('postcode')
                    else:
                        display = full
                return jsonify({"display_name": display, "full_display_name": full, "address": addr})
            except Exception:
                # continue to fallback
                pass

        # Fallback to Nominatim (OpenStreetMap) but prefer concise city/town/suburb names
        try:
            nom = requests.get("https://nominatim.openstreetmap.org/reverse", params={"format":"json","lat":lat_f,"lon":lng_f,"zoom":18,"addressdetails":1}, headers={"User-Agent":"SafePaws/1.0"}, timeout=5)
            nom.raise_for_status()
            nd = nom.json()

            # Prefer locality-level components rather than full road address
            addr = nd.get("address") or {}
            # Preferred order for locality
            locality_keys = ["city", "town", "village", "municipality", "hamlet"]
            suburb_keys = ["suburb", "quarter", "neighbourhood", "locality"]

            locality = None
            for k in locality_keys:
                if addr.get(k):
                    locality = addr.get(k)
                    break

            suburb = None
            for k in suburb_keys:
                if addr.get(k):
                    suburb = addr.get(k)
                    break

            if suburb and locality:
                display = f"{suburb}, {locality}"
            elif locality:
                display = locality
            elif suburb:
                display = suburb
            else:
                # Prefer county with postcode when available for clarity
                if addr.get('county') and addr.get('postcode'):
                    display = f"{addr.get('county')} ({addr.get('postcode')})"
                elif addr.get('county'):
                    display = addr.get('county')
                elif addr.get('state'):
                    display = addr.get('state')
                elif addr.get('postcode'):
                    display = addr.get('postcode')
                else:
                    display = nd.get('display_name')

            return jsonify({
                "display_name": display,
                "full_display_name": nd.get("display_name"),
                "address": addr,
            })
        except Exception:
            abort(502, message="Reverse geocoding failed")


@blp.route("/geocode/search")
class ForwardGeocode(MethodView):
    """Forward-geocode a query into candidate addresses (Nominatim)."""

    def get(self):
        query = request.args.get("q") or request.args.get("query")
        if not query:
            abort(400, message="q is required")

        try:
            limit = int(request.args.get("limit", 5))
        except ValueError:
            abort(400, message="limit must be an integer")
        if limit < 1 or limit > 10:
            abort(400, message="limit must be between 1 and 10")

        try:
            nom = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "json",
                    "addressdetails": 1,
                    "limit": limit,
                },
                headers={"User-Agent": "SafePaws/1.0"},
                timeout=5,
            )
            nom.raise_for_status()
            rows = nom.json()

            results = []
            for row in rows:
                results.append({
                    "display_name": row.get("display_name"),
                    "lat": row.get("lat"),
                    "lon": row.get("lon"),
                    "address": row.get("address") or {},
                })
            return jsonify({"results": results})
        except Exception:
            abort(502, message="Forward geocoding failed")


def _apply_service_filters(query, params):
    """
    Apply filtering parameters to a services query.

    Supported parameters:
    - location: substring match on location field (case-insensitive)
    - type: exact match on service type
    - max_price: services with price_per_day <= max_price
    - include_deleted: set to true to include soft-deleted services
    """
    # By default exclude soft-deleted services
    include_deleted = str(params.get('include_deleted') or '').lower() in ('1','true','yes')
    if not include_deleted:
        query = query.filter(BoardingServiceModel.is_deleted == False)

    location = params.get("location")
    if location:
        query = query.filter(
            BoardingServiceModel.location.ilike(f"%{location}%")
        )

    svc_type = params.get("type")
    if svc_type:
        query = query.filter(BoardingServiceModel.type == svc_type)

    max_price = params.get("max_price")
    if max_price is not None:
        try:
            max_price = float(max_price)
            query = query.filter(
                BoardingServiceModel.price_per_day.isnot(None),
                BoardingServiceModel.price_per_day <= max_price
            )
        except ValueError:
            abort(400, message="max_price must be a number")

    return query


def _apply_sorting(query, params):
    sort_by = (params.get("sort_by") or "").strip()
    order = (params.get("order") or "asc").lower()

    if not sort_by:
        return query

    sort_map = {
        "price_per_day": BoardingServiceModel.price_per_day,
        "name": BoardingServiceModel.name,
    }
    col = sort_map.get(sort_by)
    if col is None:
        return query

    if order == "desc":
        return query.order_by(col.desc())
    return query.order_by(col.asc())


def _apply_pagination(query, params):
    if "page" not in params and "per_page" not in params:
        return query
    try:
        page = int(params.get("page", 1))
        per_page = int(params.get("per_page", 20))
    except ValueError:
        abort(400, message="page and per_page must be integers")

    if page < 1 or per_page < 1 or per_page > 100:
        abort(400, message="page must be >= 1 and per_page between 1 and 100")

    return query.offset((page - 1) * per_page).limit(per_page)


@blp.route("/services")
class ServiceList(MethodView):
    """List all services (public) or create a service (provider)."""

    @blp.response(200, BoardingServiceSchema(many=True))
    def get(self):
        query = BoardingServiceModel.query
        query = _apply_service_filters(query, request.args)
        query = _apply_sorting(query, request.args)

        # Nearby search: provide lat & lng and set nearby=true
        lat = request.args.get("lat")
        lng = request.args.get("lng") or request.args.get("lon")
        nearby = str(request.args.get("nearby" or "")).lower() in ("1", "true", "yes")

        if nearby and lat and lng:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
            except ValueError:
                abort(400, message="Invalid lat/lng values")

            services = query.all()

            # Compute distance for services with coordinates
            services_with_dist = []
            services_without = []
            for s in services:
                if s.latitude is not None and s.longitude is not None:
                    s.distance_km = _haversine_km(lat_f, lng_f, s.latitude, s.longitude)
                    services_with_dist.append(s)
                else:
                    s.distance_km = None
                    services_without.append(s)

            # sort by distance
            services_with_dist.sort(key=lambda x: x.distance_km)

            # return services with coords first (sorted) then the rest
            return services_with_dist + services_without

        query = _apply_pagination(query, request.args)
        return query.all()

    @jwt_required()
    @blp.arguments(BoardingServiceSchema)
    @blp.response(201, BoardingServiceSchema)
    def post(self, service_data):
        # Only providers may create services
        claims = get_jwt()
        if claims.get("role") != "provider":
            abort(403, message="Only providers can create services.")

        provider_id = int(get_jwt_identity())

        # Validate capacity presence and value
        capacity = service_data.get("capacity")
        if capacity is None or not isinstance(capacity, int) or capacity < 1:
            abort(400, message="capacity is required and must be an integer >= 1")

        service = BoardingServiceModel(
            name=service_data["name"],
            description=service_data["description"],
            location=service_data["location"],
            price_per_day=service_data.get("price_per_day"),
            capacity=capacity,
            type=service_data["type"],
            services_provided=service_data.get('services_provided') or [],
            provider_id=provider_id,
            geocoded_name=service_data.get("geocoded_name"),
            geocoded_short=service_data.get("geocoded_short"),
            latitude=service_data.get("latitude"),
            longitude=service_data.get("longitude"),
        )

        # Persist provider profile updates if provided on the form
        provider = ProviderModel.query.get(provider_id)
        if provider is None:
            abort(404, message="Provider not found")

        if service_data.get('bio') is not None:
            provider.bio = service_data.get('bio')
        if service_data.get('photo_url') is not None:
            provider.photo_url = service_data.get('photo_url')

        # merge services_provided into provider.services_offered
        sp = service_data.get('services_provided') or []
        if sp:
            current = set(provider.services_offered or [])
            for item in sp:
                if item:
                    current.add(item)
            provider.services_offered = sorted(current)

        db.session.add(service)
        db.session.commit()
        return service


@blp.route("/services/<int:service_id>")
class ServiceResource(MethodView):
    """Retrieve, update, or delete a specific service."""

    @blp.response(200, BoardingServiceSchema)
    def get(self, service_id):
        return BoardingServiceModel.query.get_or_404(service_id)

    @jwt_required()
    @blp.arguments(BoardingServiceSchema)
    @blp.response(200, BoardingServiceSchema)
    def put(self, service_data, service_id):
        provider_id = int(get_jwt_identity())
        claims = get_jwt()
        if claims.get("role") != "provider":
            abort(403, message="Only providers can update services.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.provider_id != provider_id:
            abort(403, message="You can only update your own services.")

        # Validate capacity when updating
        capacity = service_data.get("capacity")
        if capacity is None or not isinstance(capacity, int) or capacity < 1:
            abort(400, message="capacity is required and must be an integer >= 1")

        service.name = service_data["name"]
        service.description = service_data["description"]
        service.location = service_data["location"]
        service.price_per_day = service_data.get("price_per_day")
        service.capacity = capacity
        service.type = service_data["type"]

        # optional geocoding information
        service.geocoded_name = service_data.get("geocoded_name")
        service.geocoded_short = service_data.get("geocoded_short")
        service.latitude = service_data.get("latitude")
        service.longitude = service_data.get("longitude")

        db.session.commit()
        return service

    @jwt_required()
    def delete(self, service_id):
        provider_id = int(get_jwt_identity())
        claims = get_jwt()
        if claims.get("role") != "provider":
            abort(403, message="Only providers can delete services.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.provider_id != provider_id:
            abort(403, message="You can only delete your own services.")

        # Soft-delete
        service.is_deleted = True
        from datetime import datetime
        service.deleted_at = datetime.utcnow()
        db.session.commit()
        return {"message": "Service deleted.", "soft_deleted": True}


@blp.route("/services/<int:service_id>/admin-delete")
class ServiceAdminDelete(MethodView):
    """Permanently delete a service (admin only)."""

    @jwt_required()
    def delete(self, service_id):
        claims = get_jwt()
        if claims.get("role") != "admin":
            abort(403, message="Only admins can permanently delete services.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        db.session.delete(service)
        db.session.commit()
        return {"message": "Service permanently deleted.", "soft_deleted": False}




@blp.route("/services/<int:service_id>/restore")
class ServiceRestore(MethodView):
    """Restore a soft-deleted service (provider only)."""

    @jwt_required()
    def post(self, service_id):
        provider_id = int(get_jwt_identity())
        claims = get_jwt()
        if claims.get("role") != "provider":
            abort(403, message="Only providers can restore services.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.provider_id != provider_id:
            abort(403, message="You can only restore your own services.")

        if not service.is_deleted:
            return {"message": "Service not deleted."}

        service.is_deleted = False
        service.deleted_at = None
        db.session.commit()
        return {"message": "Service restored."}


@blp.route("/services/<int:service_id>/reservations")
class ServiceReservations(MethodView):
    """List reservations for a specific service (provider only)."""

    @jwt_required()
    @blp.response(200, ReservationSchema(many=True))
    def get(self, service_id):
        provider_id = int(get_jwt_identity())
        claims = get_jwt()
        if claims.get("role") != "provider":
            abort(403, message="Only providers can view reservations.")

        service = BoardingServiceModel.query.get_or_404(service_id)
        if service.provider_id != provider_id:
            abort(403, message="You can only view reservations for your services.")

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
                "message": "Capacity not defined for this service."
            }

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if not start_date_str or not end_date_str:
            abort(
                400,
                message="start_date and end_date are required (YYYY-MM-DD)"
            )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            abort(400, message="Invalid date format. Use YYYY-MM-DD.")

        overlapping = ReservationModel.query.filter(
            ReservationModel.service_id == service_id,
            ReservationModel.start_date <= end_date,
            ReservationModel.end_date >= start_date,
        ).count()

        available_count = service.capacity - overlapping

        return {
            "service_id": service_id,
            "capacity": service.capacity,
            "reserved": overlapping,
            "available": max(available_count, 0),
        }
