"""Marshmallow schema for owner serialization and deserialization.

The `OwnerSchema` defines how Owner entities are exposed through the
API.  It hides the password field during serialization and requires
all necessary fields during deserialization.
"""

from marshmallow import Schema, fields, validate


class OwnerSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    email = fields.Email(required=True, validate=validate.Length(max=80))
    password = fields.Str(
        load_only=True,
        required=True,
        validate=validate.Length(min=6, max=200),
        metadata={"description": "Plain-text password; will be hashed internally"},
    )