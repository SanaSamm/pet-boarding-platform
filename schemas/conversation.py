from marshmallow import Schema, fields


class ConversationSchema(Schema):
    id = fields.Int(dump_only=True)
    owner_id = fields.Int(required=True)
    provider_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    unread_count = fields.Int(dump_only=True)
    owner_name = fields.Str(dump_only=True)
    provider_name = fields.Str(dump_only=True)


class ConversationCreateSchema(Schema):
    """Used when creating a conversation. Caller is inferred from JWT;
    client should provide the *other* participant's id (provider_id or owner_id).
    """
    owner_id = fields.Int(required=False, allow_none=True)
    provider_id = fields.Int(required=False, allow_none=True)
