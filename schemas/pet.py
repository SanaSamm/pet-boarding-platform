"""Marshmallow schema for pet serialization and deserialization.

Defines how pet objects are represented in request/response bodies.
Owner ID is required on input to associate the pet with its owner.
"""

from marshmallow import Schema, fields, validate


class PetSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    type = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    age = fields.Int(required=True, validate=validate.Range(min=0))
    owner_id = fields.Int(required=True, metadata={"description": "ID of the pet's owner"})