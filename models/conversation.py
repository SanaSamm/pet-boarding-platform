from db import db


class ConversationModel(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("owners.id"), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey("providers.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.datetime('now'))

    # messages in the conversation
    messages = db.relationship("MessageModel", back_populates="conversation", cascade="all, delete", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "owner_id": self.owner_id, "provider_id": self.provider_id}
