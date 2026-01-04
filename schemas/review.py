from marshmallow import Schema, fields, validate


class ReviewSchema(Schema):
    id = fields.Int(dump_only=True)
    reviewer_role = fields.Str(dump_only=True, allow_none=True)
    reviewer_id = fields.Int(dump_only=True, allow_none=True)
    reviewer_name = fields.Str(dump_only=True, allow_none=True)
    rating = fields.Int(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.Str(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
