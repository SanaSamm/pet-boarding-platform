from marshmallow import Schema, fields, validate


class MessageSchema(Schema):
    id = fields.Int(dump_only=True)
    conversation_id = fields.Int(allow_none=True)
    chat_room_id = fields.Int(allow_none=True)
    sender_role = fields.Str(dump_only=True)
    sender_id = fields.Int(dump_only=True)
    sender_name = fields.Str(dump_only=True)
    content = fields.Str(required=True, validate=validate.Length(min=1))
    created_at = fields.DateTime(dump_only=True)
    is_read = fields.Bool(dump_only=True)


class MessageCreateSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=1))
