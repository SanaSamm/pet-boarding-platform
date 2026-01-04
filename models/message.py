from db import db


class MessageModel(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    # Message is either part of a 1:1 conversation or a chat room
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=True)

    # Sender info
    sender_role = db.Column(db.String(20), nullable=False)  # 'owner' or 'provider'
    sender_id = db.Column(db.Integer, nullable=False)

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.datetime('now'))
    is_read = db.Column(db.Boolean, nullable=False, server_default="0")

    # Relationships
    conversation = db.relationship("ConversationModel", back_populates="messages")
    chat_room = db.relationship("ChatRoomModel", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "chat_room_id": self.chat_room_id,
            "sender_role": self.sender_role,
            "sender_id": self.sender_id,
            "content": self.content,
            "created_at": str(self.created_at),
            "is_read": bool(self.is_read),
        }
