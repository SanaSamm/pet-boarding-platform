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
    bio = fields.Str(required=False, allow_none=True)
    photo_url = fields.Str(required=False, allow_none=True)



class ProviderProfileSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    bio = fields.Str(allow_none=True)
    photo_url = fields.Str(allow_none=True)
    average_rating = fields.Float(dump_only=True, allow_none=True)
    services = fields.List(fields.Dict())  # simple dicts with id/name/price
    provided_services = fields.List(fields.Str(), dump_only=True)
    highlights = fields.Str(dump_only=True, allow_none=True)


class ProviderListItemSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    bio = fields.Str(allow_none=True)
    photo_url = fields.Str(allow_none=True)
    average_rating = fields.Float(dump_only=True, allow_none=True)
    highlights = fields.Str(dump_only=True, allow_none=True)


class ProviderUpdateSchema(Schema):
    bio = fields.Str(required=False, allow_none=True)
    photo_url = fields.Str(required=False, allow_none=True)
    # Allow provider to edit their declared services (list of strings)
    services_offered = fields.List(fields.Str(), required=False, allow_none=True)
