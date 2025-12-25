"""Pet management blueprint.

Owners can create, list, and delete their pets.  All routes in this
blueprint require an authenticated owner.  Pets belong exclusively to
their owner and cannot be managed by other owners or providers.
"""

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from db import db
from models.pet import PetModel
from models.owner import OwnerModel
from schemas.pet import PetSchema

blp = Blueprint(
    "Pets", __name__, description="Operations on pets (owner-only)"
)


@blp.route("/pets")
class PetsList(MethodView):
    """Endpoint to list and create pets for the current owner."""

    @jwt_required()
    @blp.response(200, PetSchema(many=True))
    def get(self):
        # Ensure the requester is an owner
        identity = get_jwt_identity()
        if identity.get("role") != "owner":
            abort(403, message="Only owners can view their pets.")

        owner_id = identity["id"]
        owner = OwnerModel.query.get_or_404(owner_id)
        return owner.pets.all()

    @jwt_required()
    @blp.arguments(PetSchema)
    @blp.response(201, PetSchema)
    def post(self, pet_data):
        # Ensure the requester is an owner
        identity = get_jwt_identity()
        if identity.get("role") != "owner":
            abort(403, message="Only owners can create pets.")

        # Assign the current owner ID
        pet = PetModel(
            name=pet_data["name"],
            type=pet_data["type"],
            age=pet_data["age"],
            owner_id=identity["id"],
        )
        db.session.add(pet)
        db.session.commit()
        return pet


@blp.route("/pets/<int:pet_id>")
class PetResource(MethodView):
    """Endpoint to delete a specific pet (owner-only)."""

    @jwt_required()
    def delete(self, pet_id):
        identity = get_jwt_identity()
        if identity.get("role") != "owner":
            abort(403, message="Only owners can delete pets.")

        pet = PetModel.query.get_or_404(pet_id)
        if pet.owner_id != identity["id"]:
            abort(403, message="You do not have permission to delete this pet.")

        db.session.delete(pet)
        db.session.commit()
        return {"message": "Pet deleted."}