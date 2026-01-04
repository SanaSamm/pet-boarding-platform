"""
Pet management blueprint.

Owners can create, list, and delete their pets.
All routes require authentication.
Pets belong exclusively to their owner.
"""
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from db import db
from models.pet import PetModel
from models.owner import OwnerModel
from schemas.pet import PetSchema, PetCreateSchema

blp = Blueprint("Pets", __name__, description="Owner pets")


@blp.route("/pets")
class PetsList(MethodView):

    # ---------- GET /pets ----------
    @jwt_required()
    @blp.response(200, PetSchema(many=True))
    def get(self):
        owner_id = int(get_jwt_identity())
        claims = get_jwt()

        if claims.get("role") != "owner":
            abort(403, message="Only owners can view pets")

        owner = OwnerModel.query.get_or_404(owner_id)
        return owner.pets.all()

    # ---------- POST /pets ----------
    @jwt_required()
    @blp.arguments(PetCreateSchema)
    @blp.response(201, PetSchema)
    def post(self, pet_data):
        owner_id = int(get_jwt_identity())
        claims = get_jwt()

        if claims.get("role") != "owner":
            abort(403, message="Only owners can create pets")

        pet = PetModel(
            name=pet_data["name"],
            type=pet_data["type"],
            age=pet_data["age"],
            owner_id=owner_id   # 👈 FROM JWT ONLY
        )

        db.session.add(pet)
        db.session.commit()
        return pet

