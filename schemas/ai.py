from marshmallow import Schema, fields


class ConciergeRequestSchema(Schema):
    query = fields.Str(required=True)
    location = fields.Str(required=False, allow_none=True)
    service_keyword = fields.Str(required=False, allow_none=True)
    max_price = fields.Float(required=False, allow_none=True)
    lat = fields.Float(required=False, allow_none=True)
    lng = fields.Float(required=False, allow_none=True)
    lon = fields.Float(required=False, allow_none=True)


class ConciergeResultSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    location = fields.Str()
    price_per_day = fields.Float(allow_none=True)
    provider_id = fields.Int()
    services_provided = fields.List(fields.Str())
    distance_km = fields.Float(allow_none=True)
    highlights = fields.Str(allow_none=True)


class ConciergeResponseSchema(Schema):
    query = fields.Str()
    interpreted = fields.Dict()
    answer = fields.Str()
    results = fields.List(fields.Nested(ConciergeResultSchema))
