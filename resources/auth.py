"""
Authentication blueprint for the Pet Boarding API.

This blueprint exposes endpoints for registering and logging in owners
and providers. Passwords are hashed using Passlib before being stored.
Upon successful login, a JWT access token is returned with the user's
ID and role encoded in the identity.
"""

from flask.views import MethodView
import hmac
import os
from flask_smorest import Blueprint, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from passlib.hash import pbkdf2_sha256

from db import db
from models.owner import OwnerModel
from models.provider import ProviderModel
from schemas.owner import OwnerSchema
from schemas.provider import ProviderSchema
from schemas.login import LoginSchema


blp = Blueprint(
    "Auth", __name__, description="Authentication for owners and providers"
)


# -------------------------------------------------
# OWNER REGISTER
# -------------------------------------------------
@blp.route("/owner/register")
class OwnerRegister(MethodView):
    """Endpoint for owner registration."""

    @blp.arguments(OwnerSchema)
    @blp.response(201, OwnerSchema)
    def post(self, owner_data):
        if OwnerModel.query.filter_by(email=owner_data["email"]).first() or \
           ProviderModel.query.filter_by(email=owner_data["email"]).first():
            abort(409, message="A user with that email already exists.")

        owner = OwnerModel(
            name=owner_data["name"],
            email=owner_data["email"],
            password=pbkdf2_sha256.hash(owner_data["password"]),
        )

        db.session.add(owner)
        db.session.commit()
        return owner


# -------------------------------------------------
# OWNER LOGIN
# -------------------------------------------------
@blp.route("/owner/login")
class OwnerLogin(MethodView):

    @blp.arguments(LoginSchema)
    def post(self, login_data):
        owner = OwnerModel.query.filter_by(email=login_data["email"]).first()

        if not owner or not pbkdf2_sha256.verify(
            login_data["password"], owner.password
        ):
            abort(401, message="Invalid email or password")

        access_token = create_access_token(
            identity=str(owner.id),
            additional_claims={"role": "owner"}
        )
        return {"access_token": access_token}


# -------------------------------------------------
# PROVIDER REGISTER
# -------------------------------------------------
@blp.route("/provider/register")
class ProviderRegister(MethodView):
    """Endpoint for provider registration."""

    @blp.arguments(ProviderSchema)
    @blp.response(201, ProviderSchema)
    def post(self, provider_data):
        if OwnerModel.query.filter_by(email=provider_data["email"]).first() or \
           ProviderModel.query.filter_by(email=provider_data["email"]).first():
            abort(409, message="A user with that email already exists.")

        provider = ProviderModel(
            name=provider_data["name"],
            email=provider_data["email"],
            password=pbkdf2_sha256.hash(provider_data["password"]),
        )

        db.session.add(provider)
        db.session.commit()
        return provider


# -------------------------------------------------
# PROVIDER LOGIN
# -------------------------------------------------
@blp.route("/provider/login")
class ProviderLogin(MethodView):

    @blp.arguments(LoginSchema)
    def post(self, login_data):
        provider = ProviderModel.query.filter_by(email=login_data["email"]).first()

        if not provider or not pbkdf2_sha256.verify(
            login_data["password"], provider.password
        ):
            abort(401, message="Invalid email or password")

        access_token = create_access_token(
            identity=str(provider.id),
            additional_claims={"role": "provider"}
        )

        # Decide where to redirect the provider after login:
        # - if provider has services, send them to their profile
        # - otherwise send them to the offer-care page to create their first service
        has_services = False
        service_count = 0
        try:
            # Count any historical services (including soft-deleted). If provider ever created services,
            # treat them as an "existing" provider and send them to their profile page so they can
            # review or restore services. This matches user expectations.
            from models.service import BoardingServiceModel
            service_count = BoardingServiceModel.query.filter_by(provider_id=provider.id).count()
            has_services = service_count > 0
        except Exception:
            # On any error, default to sending user to /offer-care (safe choice)
            has_services = False
            service_count = 0

        next_url = f"/provider?id={provider.id}" if has_services else "/offer-care"

        # Return metadata for debugging/client use
        return {"access_token": access_token, "next": next_url, "has_services": has_services, "service_count": service_count}


@blp.route("/admin/login")
class AdminLogin(MethodView):
    """Login for admin users via environment credentials."""

    @blp.arguments(LoginSchema)
    def post(self, login_data):
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_email or not admin_password:
            abort(403, message="Admin login is not configured.")

        email_ok = hmac.compare_digest(admin_email, login_data["email"])
        pass_ok = hmac.compare_digest(admin_password, login_data["password"])
        if not (email_ok and pass_ok):
            abort(401, message="Invalid email or password")

        access_token = create_access_token(
            identity="0",
            additional_claims={"role": "admin"}
        )
        return {"access_token": access_token}


@blp.route('/me')
class WhoAmI(MethodView):

    @jwt_required()
    def get(self):
        """Return authenticated principal id and role."""
        claims = get_jwt()
        user_id = int(get_jwt_identity())
        role = claims.get("role")
        name = None
        if role == "owner":
            owner = OwnerModel.query.get(user_id)
            name = owner.name if owner else None
        elif role == "provider":
            provider = ProviderModel.query.get(user_id)
            name = provider.name if provider else None
        elif role == "admin":
            name = "Admin"
        return {"id": user_id, "role": role, "name": name}
