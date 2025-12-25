"""
Main application factory for the Pet Boarding API.

This module exposes a `create_app` function that constructs the Flask
application with all necessary configuration, extensions, and blueprints.
It configures SQLAlchemy for SQLite, JWT for authentication, and
Swagger/OpenAPI using Flask-Smorest.
"""

from flask import Flask
from flask_smorest import Api
from flask_jwt_extended import JWTManager

from db import db


def create_app() -> Flask:
    """Application factory function."""
    app = Flask(__name__)

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///petboarding.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Swagger / OpenAPI configuration
    app.config["API_TITLE"] = "Pet Boarding REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    # JWT configuration
    app.config["JWT_SECRET_KEY"] = "super-secret"  # change in production

    # Initialize extensions
    db.init_app(app)
    api = Api(app)
    JWTManager(app)

    # Import and register blueprints
    from resources.auth import blp as AuthBlueprint
    from resources.pets import blp as PetsBlueprint
    from resources.services import blp as ServicesBlueprint
    from resources.reservations import blp as ReservationsBlueprint

    api.register_blueprint(AuthBlueprint)
    api.register_blueprint(PetsBlueprint)
    api.register_blueprint(ServicesBlueprint)
    api.register_blueprint(ReservationsBlueprint)

    return app


if __name__ == "__main__":
    app = create_app()

    # Create database tables once at startup (Flask 3 compatible)
    with app.app_context():
        db.create_all()

    app.run(port=5000, debug=True)
