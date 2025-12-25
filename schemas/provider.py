"""Marshmallow schema for provider serialization and deserialization.

Providers represent businesses or individuals offering boarding services.
Passwords are hidden during serialization and required during load.
"""

from marshmallow import Schema, fields, validate


class ProviderSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    email = fields.Email(required=True, validate=validate.Length(max=80))
    password = fields.Str(
        load_only=True,
        required=True,
        validate=validate.Length(min=6, max=200),
        metadata={"description": "Plain-text password; will be hashed internally"},
    )