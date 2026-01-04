from flask_smorest import Blueprint
from flask import jsonify

blp = Blueprint(
    "Health",
    "health",
    url_prefix="/api",
    description="Health check"
)

@blp.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "Backend is running"
    })

