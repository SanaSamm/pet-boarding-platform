"""Marshmallow schema for boarding service serialization and deserialization.

Boarding services belong to providers and include optional fields for
price and capacity.
"""

from marshmallow import Schema, fields, validate


class BoardingServiceSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    location = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    price_per_day = fields.Float(allow_none=True)
    capacity = fields.Int(allow_none=True, validate=validate.Range(min=0))
    type = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    provider_id = fields.Int(required=True, metadata={"description": "ID of the service's provider"})