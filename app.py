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

    @app.route("/")
    def index():
        from flask import render_template
        return render_template("index.html")

    @app.route("/find-care")
    def find_care():
        from flask import render_template
        return render_template("find_care.html")

    @app.route("/offer-care")
    def offer_care():
        from flask import render_template
        return render_template("offer_care.html")

    @app.route("/login")
    def login():
        from flask import render_template
        return render_template("login.html")

    @app.route("/register")
    def register():
        from flask import render_template
        return render_template("register.html")

    @app.route("/service-details")
    def service_details():
        from flask import render_template
        return render_template("details.html")

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

    app.run(host="0.0.0.0", port=5000, debug=True)
