"""Marshmallow schema for boarding service serialization and deserialization.

Boarding services belong to providers and include optional fields for
price and capacity.
"""

from marshmallow import Schema, fields, validate

class BoardingServiceSchema(Schema):
    id = fields.Int(dump_only=True)

    name = fields.Str(required=True)
    description = fields.Str(required=True)
    location = fields.Str(required=True)

    price_per_day = fields.Float(required=False, allow_none=True)
    # Capacity is required and must be at least 1
    capacity = fields.Int(required=True, validate=validate.Range(min=1))

    type = fields.Str(required=True)

    services_provided = fields.List(
        fields.Str(),
        required=False
    )

    # provider_id is inferred from the authenticated provider creating the service
    provider_id = fields.Int(required=False, allow_none=True)

    # Allow providers to submit/update profile info when creating a service
    bio = fields.Str(required=False, allow_none=True)
    photo_url = fields.Str(required=False, allow_none=True)

    # Geocoding fields: optional when provider adds exact location
    geocoded_name = fields.Str(required=False, allow_none=True)
    geocoded_short = fields.Str(required=False, allow_none=True)
    latitude = fields.Float(required=False, allow_none=True)
    longitude = fields.Float(required=False, allow_none=True)

    # Distance is computed when searching by proximity (dump-only)
    distance_km = fields.Float(dump_only=True, allow_none=True)

    # Soft-delete flag (dump-only)
    is_deleted = fields.Bool(dump_only=True)
    deleted_at = fields.DateTime(dump_only=True, allow_none=True) 
