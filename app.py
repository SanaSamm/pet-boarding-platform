"""
Main application factory for the Pet Boarding API.
"""
from flask import Flask
from flask_smorest import Api
from flask_jwt_extended import JWTManager

from db import db
from sqlalchemy import text
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError


def create_app() -> Flask:
    """Application factory function."""
    app = Flask(__name__)

    # --------------------
    # Configuration
    # --------------------
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///petboarding.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["API_TITLE"] = "Pet Boarding REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    app.config["JWT_SECRET_KEY"] = "super-secret"  # change in production

    # --------------------
    # Extensions
    # --------------------
    db.init_app(app)
    api = Api(app)
    JWTManager(app)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return {
            "message": exc.description,
            "error": {
                "code": exc.name.replace(" ", "_").lower(),
                "status": exc.code,
            },
        }, exc.code

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc):
        return {
            "message": "Validation error",
            "error": {
                "code": "validation_error",
                "status": 400,
                "details": exc.messages,
            },
        }, 400

    # --------------------
    # UI Routes (Pages)
    # --------------------
    from flask import render_template

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/find-care")
    def find_care():
        return render_template("find_care.html")

    @app.route("/offer-care")
    def offer_care():
        return render_template("offer_care.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/register")
    def register():
        return render_template("register.html")

    @app.route("/service-details")
    def service_details():
        return render_template("details.html")

    @app.route("/provider")
    def provider():
        return render_template("provider.html")

    @app.route("/create-pet")
    def create_pet():
        return render_template("create_pet.html")

    @app.route("/messages")
    def messages_page():
        return render_template("messages.html")

    @app.route("/community")
    def community_page():
        return render_template("community.html")

    # ----- Debug: quick helper for local development -----
    @app.route('/debug/service-provider')
    def debug_service_provider():
        from flask import request, jsonify
        from models.service import BoardingServiceModel
        from models.provider import ProviderModel

        sid = request.args.get('id')
        if not sid:
            return jsonify({"error": "id required"}), 400
        try:
            sid = int(sid)
        except ValueError:
            return jsonify({"error": "invalid id"}), 400

        service = BoardingServiceModel.query.get(sid)
        if not service:
            return jsonify({"error": "service not found"}), 404

        provider = ProviderModel.query.get(service.provider_id)
        return jsonify({
            "service": {"id": service.id, "name": service.name, "provider_id": service.provider_id, "keys": list(service.__dict__.keys())},
            "provider": {"exists": bool(provider), "id": provider.id if provider else None, "name": provider.name if provider else None, "bio": provider.bio if provider else None}
        })

    @app.route("/my-pets")
    def my_pets():
      return render_template("my_pets.html")

    # --------------------
    # API Blueprints
    # --------------------
    from resources.health import blp as HealthBlueprint
    from resources.auth import blp as AuthBlueprint
    from resources.owners import blp as OwnersBlueprint
    from resources.pets import blp as PetsBlueprint
    from resources.services import blp as ServicesBlueprint
    from resources.reservations import blp as ReservationsBlueprint
    from resources.providers import blp as ProvidersBlueprint
    from resources.reviews import blp as ReviewsBlueprint
    from resources.messages import blp as MessagesBlueprint
    from resources.ai import blp as AIBlueprint

    api.register_blueprint(HealthBlueprint)
    api.register_blueprint(AuthBlueprint)
    api.register_blueprint(OwnersBlueprint)
    api.register_blueprint(PetsBlueprint)
    api.register_blueprint(ServicesBlueprint)
    api.register_blueprint(ReservationsBlueprint)
    api.register_blueprint(ProvidersBlueprint)
    api.register_blueprint(ReviewsBlueprint)
    api.register_blueprint(MessagesBlueprint)
    api.register_blueprint(AIBlueprint)

    return app


# --------------------
# Entry point
# --------------------
if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        def _ensure_provider_columns():
            def _should_ignore_migration_error(err):
                msg = str(err).lower()
                return ("no such table" in msg) or ("duplicate column name" in msg)

            # Add newly introduced columns to providers table if they are missing.
            # This is a small development-time migration helper. For production use Alembic.
            conn = db.engine.connect()
            try:
                try:
                    res = conn.execute("PRAGMA table_info('providers')").fetchall()
                    cols = [row['name'] for row in res]
                except Exception:
                    cols = []

                if 'bio' not in cols:
                    try:
                        print("Applying migration: add providers.bio")
                        conn.execute(text("ALTER TABLE providers ADD COLUMN bio TEXT"))
                    except Exception as e:
                        if not _should_ignore_migration_error(e):
                            print("Failed to add providers.bio:", e)
                if 'photo_url' not in cols:
                    try:
                        print("Applying migration: add providers.photo_url")
                        conn.execute(text("ALTER TABLE providers ADD COLUMN photo_url VARCHAR(255)"))
                    except Exception as e:
                        if not _should_ignore_migration_error(e):
                            print("Failed to add providers.photo_url:", e)
                if 'services_offered' not in cols:
                    try:
                        print("Applying migration: add providers.services_offered")
                        conn.execute(text("ALTER TABLE providers ADD COLUMN services_offered TEXT"))
                    except Exception as e:
                        if not _should_ignore_migration_error(e):
                            print("Failed to add providers.services_offered:", e)

                # Ensure boarding_services has geolocation & soft-delete columns (dev migration helper)
                try:
                    res2 = conn.execute("PRAGMA table_info('boarding_services')").fetchall()
                    svc_cols = [row['name'] for row in res2]
                except Exception:
                    svc_cols = []

                added = []
                try:
                    if 'geocoded_name' not in svc_cols:
                        print('Applying migration: add boarding_services.geocoded_name')
                        conn.execute(text("ALTER TABLE boarding_services ADD COLUMN geocoded_name TEXT"))
                        added.append('geocoded_name')
                    if 'latitude' not in svc_cols:
                        print('Applying migration: add boarding_services.latitude')
                        conn.execute(text("ALTER TABLE boarding_services ADD COLUMN latitude FLOAT"))
                        added.append('latitude')
                    if 'longitude' not in svc_cols:
                        print('Applying migration: add boarding_services.longitude')
                        conn.execute(text("ALTER TABLE boarding_services ADD COLUMN longitude FLOAT"))
                        added.append('longitude')
                    if 'geocoded_short' not in svc_cols:
                        print('Applying migration: add boarding_services.geocoded_short')
                        conn.execute(text("ALTER TABLE boarding_services ADD COLUMN geocoded_short TEXT"))
                        added.append('geocoded_short')
                    if 'is_deleted' not in svc_cols:
                        print('Applying migration: add boarding_services.is_deleted')
                        conn.execute(text("ALTER TABLE boarding_services ADD COLUMN is_deleted INTEGER DEFAULT 0"))
                        added.append('is_deleted')
                    if 'deleted_at' not in svc_cols:
                        print('Applying migration: add boarding_services.deleted_at')
                        conn.execute(text("ALTER TABLE boarding_services ADD COLUMN deleted_at DATETIME"))
                        added.append('deleted_at')
                except Exception as e:
                    if not _should_ignore_migration_error(e):
                        print('Failed to apply boarding_services migrations:', e)

                if added:
                    print('Added boarding_services columns:', ', '.join(added))

                # Migrate reviews table to support reviewer_role/reviewer_id and make owner_id nullable
                try:
                    res = conn.execute("PRAGMA table_info('reviews')").fetchall()
                    review_cols = [row['name'] for row in res]
                except Exception:
                    review_cols = []

                if 'reviewer_role' not in review_cols or 'reviewer_id' not in review_cols or ('owner_id' in review_cols and any(row['notnull']==1 and row['name']=='owner_id' for row in res)):
                    try:
                        print('Applying reviews migration: add reviewer_role/reviewer_id and make owner_id nullable')
                        conn.execute(text("CREATE TABLE IF NOT EXISTS reviews_new (id INTEGER PRIMARY KEY, owner_id INTEGER, reviewer_role TEXT, reviewer_id INTEGER, provider_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at DATETIME)"))
                        # Copy existing data: set reviewer_role='owner' and reviewer_id=owner_id
                        conn.execute(text("INSERT INTO reviews_new (id, owner_id, reviewer_role, reviewer_id, provider_id, rating, comment, created_at) SELECT id, owner_id, 'owner', owner_id, provider_id, rating, comment, created_at FROM reviews"))
                        conn.execute(text("DROP TABLE IF EXISTS reviews"))
                        conn.execute(text("ALTER TABLE reviews_new RENAME TO reviews"))
                    except Exception as e:
                        if not _should_ignore_migration_error(e):
                            print('Failed to migrate reviews:', e)
                        # swallow; db will create table later via SQLAlchemy models

                # Create indexes for frequent lookups (SQLite)
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reservations_service_id ON reservations(service_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_services_provider_id ON boarding_services(provider_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_services_is_deleted ON boarding_services(is_deleted)"))
                except Exception as e:
                    if not _should_ignore_migration_error(e):
                        print("Failed to create indexes:", e)

                # Ensure messages.is_read exists for unread badge logic
                try:
                    msg_res = conn.execute("PRAGMA table_info('messages')").fetchall()
                    msg_cols = [row['name'] for row in msg_res]
                except Exception:
                    msg_cols = []

                if 'is_read' not in msg_cols:
                    try:
                        print("Applying migration: add messages.is_read")
                        conn.execute(text("ALTER TABLE messages ADD COLUMN is_read BOOLEAN DEFAULT 0"))
                    except Exception as e:
                        if not _should_ignore_migration_error(e):
                            print("Failed to add messages.is_read:", e)


            finally:
                conn.close()

        print("\n=== SQLAlchemy tables detected ===")
        for table_name in db.metadata.tables.keys():
            print(table_name)
        print("=================================\n")

        # Run lightweight migrations (dev only) then create any missing tables
        _ensure_provider_columns()
        db.create_all()

        # Ensure the public owners chat room exists
        try:
            from models.chat_room import ChatRoomModel
            if not ChatRoomModel.query.filter_by(name='owners').first():
                db.session.add(ChatRoomModel(name='owners', description='Shared chat for pet owners'))
                db.session.commit()
        except Exception:
            pass

    app.run(host="0.0.0.0", port=5000, debug=True)
