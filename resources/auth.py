"""Authentication blueprint for the Pet Boarding API.

This blueprint exposes endpoints for registering and logging in owners
and providers.  Passwords are hashed using Passlib before being
stored.  Upon successful login, a JWT access token is returned with
the user's ID and role encoded in the identity.
"""

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token
from passlib.hash import pbkdf2_sha256

from db import db
from models.owner import OwnerModel
from models.provider import ProviderModel
from schemas.owner import OwnerSchema
from schemas.provider import ProviderSchema


blp = Blueprint(
    "Auth", __name__, description="Authentication for owners and providers"
)


@blp.route("/owner/register")
class OwnerRegister(MethodView):
    """Endpoint for owner registration."""

    @blp.arguments(OwnerSchema)
    @blp.response(201, OwnerSchema)
    def post(self, owner_data):
        # Check if email already exists among owners or providers
        if OwnerModel.query.filter_by(email=owner_data["email"]).first() or \
           ProviderModel.query.filter_by(email=owner_data["email"]).first():
            abort(409, message="A user with that email already exists.")

        # Hash the plain-text password
        hashed_pw = pbkdf2_sha256.hash(owner_data["password"])
        owner = OwnerModel(
            name=owner_data["name"],
            email=owner_data["email"],
            password=hashed_pw,
        )
        db.session.add(owner)
        db.session.commit()
        return owner


@blp.route("/owner/login")
class OwnerLogin(MethodView):
    """Endpoint for owner login."""

    @blp.arguments(OwnerSchema)
    def post(self, owner_data):
        owner = OwnerModel.query.filter_by(email=owner_data["email"]).first()
        if not owner or not pbkdf2_sha256.verify(owner_data["password"], owner.password):
            abort(401, message="Invalid email or password")

        access_token = create_access_token(
            identity={"id": owner.id, "role": "owner"}
        )
        return {"access_token": access_token}


@blp.route("/provider/register")
class ProviderRegister(MethodView):
    """Endpoint for provider registration."""

    @blp.arguments(ProviderSchema)
    @blp.response(201, ProviderSchema)
    def post(self, provider_data):
        # Check if email already exists among owners or providers
        if OwnerModel.query.filter_by(email=provider_data["email"]).first() or \
           ProviderModel.query.filter_by(email=provider_data["email"]).first():
            abort(409, message="A user with that email already exists.")

        hashed_pw = pbkdf2_sha256.hash(provider_data["password"])
        provider = ProviderModel(
            name=provider_data["name"],
            email=provider_data["email"],
            password=hashed_pw,
        )
        db.session.add(provider)
        db.session.commit()
        return provider


@blp.route("/provider/login")
class ProviderLogin(MethodView):
    """Endpoint for provider login."""

    @blp.arguments(ProviderSchema)
    def post(self, provider_data):
        provider = ProviderModel.query.filter_by(email=provider_data["email"]).first()
        if not provider or not pbkdf2_sha256.verify(provider_data["password"], provider.password):
            abort(401, message="Invalid email or password")

        access_token = create_access_token(
            identity={"id": provider.id, "role": "provider"}
        )
        return {"access_token": access_token}