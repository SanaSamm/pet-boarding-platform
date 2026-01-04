from db import db


class ChatRoomModel(db.Model):
    __tablename__ = "chat_rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.datetime('now'))

    messages = db.relationship("MessageModel", back_populates="chat_room", cascade="all, delete", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}
