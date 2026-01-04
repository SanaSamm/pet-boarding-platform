"""Marshmallow schema for pet serialization and deserialization.

Defines how pet objects are represented in request/response bodies.
Owner ID is required on input to associate the pet with its owner.
"""
from marshmallow import Schema, fields, validate

# Used for OUTPUT only (GET responses)
class PetSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    type = fields.Str()
    age = fields.Int()


# Used for INPUT only (POST /pets)
class PetCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1))
    type = fields.Str(required=True, validate=validate.Length(min=1))
    age = fields.Int(required=True, validate=validate.Range(min=0))
