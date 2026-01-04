from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from db import db
from models.conversation import ConversationModel
from models.message import MessageModel
from models.chat_room import ChatRoomModel
from models.owner import OwnerModel
from models.provider import ProviderModel
from schemas.conversation import ConversationSchema, ConversationCreateSchema
from schemas.message import MessageSchema, MessageCreateSchema
from schemas.chat_room import ChatRoomSchema

blp = Blueprint("Messages", __name__, description="Messaging between owners and providers and community chat")


@blp.route("/conversations")
class ConversationsList(MethodView):
    @jwt_required()
    @blp.response(200, ConversationSchema(many=True))
    def get(self):
        claims = get_jwt()
        role = claims.get("role")
        user_id = int(get_jwt_identity())

        if role == "owner":
            convos = ConversationModel.query.filter_by(owner_id=user_id).all()
        elif role == "provider":
            convos = ConversationModel.query.filter_by(provider_id=user_id).all()
        else:
            abort(403, message="Invalid role")

        # Attach participant display names
        owner_ids = {c.owner_id for c in convos}
        provider_ids = {c.provider_id for c in convos}
        owners = {o.id: o.name for o in OwnerModel.query.filter(OwnerModel.id.in_(owner_ids)).all()} if owner_ids else {}
        providers = {p.id: p.name for p in ProviderModel.query.filter(ProviderModel.id.in_(provider_ids)).all()} if provider_ids else {}

        # Attach unread counts for the current user
        for convo in convos:
            unread = MessageModel.query.filter(
                MessageModel.conversation_id == convo.id,
                MessageModel.sender_role != role,
                MessageModel.is_read == False
            ).count()
            setattr(convo, "unread_count", unread)
            setattr(convo, "owner_name", owners.get(convo.owner_id))
            setattr(convo, "provider_name", providers.get(convo.provider_id))

        return convos

    @jwt_required()
    @blp.arguments(ConversationCreateSchema)
    @blp.response(201, ConversationSchema)
    def post(self, convo_data):
        # Infer caller from JWT
        claims = get_jwt()
        role = claims.get("role")
        user_id = int(get_jwt_identity())

        owner_id = convo_data.get("owner_id")
        provider_id = convo_data.get("provider_id")

        if role == "owner":
            owner_id = user_id
            if not provider_id:
                abort(400, message="provider_id is required when creating a conversation as an owner")
        elif role == "provider":
            provider_id = user_id
            if not owner_id:
                abort(400, message="owner_id is required when creating a conversation as a provider")
        else:
            abort(403, message="Invalid role")

        # Ensure participants exist
        owner = OwnerModel.query.get(owner_id)
        provider = ProviderModel.query.get(provider_id)
        if not owner or not provider:
            abort(404, message="Owner or provider not found")

        # Try to find existing conversation
        convo = ConversationModel.query.filter_by(owner_id=owner.id, provider_id=provider.id).first()
        if convo:
            return convo

        convo = ConversationModel(owner_id=owner.id, provider_id=provider.id)
        db.session.add(convo)
        db.session.commit()
        return convo


@blp.route("/conversations/<int:conversation_id>/messages")
class ConversationMessages(MethodView):
    @jwt_required()
    @blp.response(200, MessageSchema(many=True))
    def get(self, conversation_id):
        claims = get_jwt()
        role = claims.get("role")
        user_id = int(get_jwt_identity())

        convo = ConversationModel.query.get(conversation_id)
        if not convo:
            abort(404, message="Conversation not found")

        # authorization: only participants may view
        if not ((role == "owner" and convo.owner_id == user_id) or (role == "provider" and convo.provider_id == user_id)):
            abort(403, message="You are not a participant in this conversation")

        # Mark unread messages as read for the current participant
        MessageModel.query.filter(
            MessageModel.conversation_id == conversation_id,
            MessageModel.sender_role != role,
            MessageModel.is_read == False
        ).update({"is_read": True})
        db.session.commit()

        messages = MessageModel.query.filter_by(conversation_id=conversation_id).order_by(MessageModel.created_at.asc()).all()

        owner_ids = {m.sender_id for m in messages if m.sender_role == "owner"}
        provider_ids = {m.sender_id for m in messages if m.sender_role == "provider"}
        owners = {o.id: o.name for o in OwnerModel.query.filter(OwnerModel.id.in_(owner_ids)).all()} if owner_ids else {}
        providers = {p.id: p.name for p in ProviderModel.query.filter(ProviderModel.id.in_(provider_ids)).all()} if provider_ids else {}

        for m in messages:
            if m.sender_role == "owner":
                setattr(m, "sender_name", owners.get(m.sender_id))
            elif m.sender_role == "provider":
                setattr(m, "sender_name", providers.get(m.sender_id))

        return messages

    @jwt_required()
    @blp.arguments(MessageCreateSchema)
    @blp.response(201, MessageSchema)
    def post(self, message_data, conversation_id):
        claims = get_jwt()
        role = claims.get("role")
        user_id = int(get_jwt_identity())

        convo = ConversationModel.query.get(conversation_id)
        if not convo:
            abort(404, message="Conversation not found")

        if not ((role == "owner" and convo.owner_id == user_id) or (role == "provider" and convo.provider_id == user_id)):
            abort(403, message="You are not a participant in this conversation")

        # Ensure message is tied to conversation & has content
        content = message_data.get("content")
        if not content:
            abort(400, message="content is required")

        msg = MessageModel(conversation_id=convo.id, sender_role=role, sender_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()
        if role == "owner":
            owner = OwnerModel.query.get(user_id)
            if owner:
                setattr(msg, "sender_name", owner.name)
        elif role == "provider":
            provider = ProviderModel.query.get(user_id)
            if provider:
                setattr(msg, "sender_name", provider.name)
        return msg


@blp.route("/chat/rooms")
class ChatRoomsList(MethodView):
    @jwt_required()
    @blp.response(200, ChatRoomSchema(many=True))
    def get(self):
        # return all chat rooms (public)
        rooms = ChatRoomModel.query.all()
        return rooms

    @jwt_required()
    @blp.arguments(ChatRoomSchema)
    @blp.response(201, ChatRoomSchema)
    def post(self, room_data):
        # allow creation of room for now by any logged-in user
        room = ChatRoomModel(name=room_data["name"], description=room_data.get("description"))
        db.session.add(room)
        db.session.commit()
        return room


@blp.route("/chat/rooms/<int:room_id>/messages")
class ChatRoomMessages(MethodView):
    @jwt_required()
    @blp.response(200, MessageSchema(many=True))
    def get(self, room_id):
        room = ChatRoomModel.query.get(room_id)
        if not room:
            abort(404, message="Chat room not found")
        messages = MessageModel.query.filter_by(chat_room_id=room_id).order_by(MessageModel.created_at.asc()).all()
        owner_ids = {m.sender_id for m in messages if m.sender_role == "owner"}
        provider_ids = {m.sender_id for m in messages if m.sender_role == "provider"}
        owners = {o.id: o.name for o in OwnerModel.query.filter(OwnerModel.id.in_(owner_ids)).all()} if owner_ids else {}
        providers = {p.id: p.name for p in ProviderModel.query.filter(ProviderModel.id.in_(provider_ids)).all()} if provider_ids else {}
        for m in messages:
            if m.sender_role == "owner":
                setattr(m, "sender_name", owners.get(m.sender_id))
            elif m.sender_role == "provider":
                setattr(m, "sender_name", providers.get(m.sender_id))
        return messages

    @jwt_required()
    @blp.arguments(MessageCreateSchema)
    @blp.response(201, MessageSchema)
    def post(self, message_data, room_id):
        claims = get_jwt()
        role = claims.get("role")
        user_id = int(get_jwt_identity())

        # Restrict sending to owners only for shared owners chat
        room = ChatRoomModel.query.get(room_id)
        if not room:
            abort(404, message="Chat room not found")

        if role != "owner":
            abort(403, message="Only owners can post to community chat")

        content = message_data.get("content")
        if not content:
            abort(400, message="content is required")

        msg = MessageModel(chat_room_id=room.id, sender_role=role, sender_id=user_id, content=content)
        db.session.add(msg)
        db.session.commit()
        if role == "owner":
            owner = OwnerModel.query.get(user_id)
            if owner:
                setattr(msg, "sender_name", owner.name)
        elif role == "provider":
            provider = ProviderModel.query.get(user_id)
            if provider:
                setattr(msg, "sender_name", provider.name)
        return msg
