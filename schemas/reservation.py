"""Marshmallow schema for reservation serialization and deserialization.

Reservations link pets with services for a specified date range.
"""

from marshmallow import Schema, fields


class ReservationSchema(Schema):
    id = fields.Int(dump_only=True)
    start_date = fields.Date(required=True, metadata={"description": "Start date of the stay"})
    end_date = fields.Date(required=True, metadata={"description": "End date of the stay"})
    pet_id = fields.Int(required=True)
    service_id = fields.Int(required=True)