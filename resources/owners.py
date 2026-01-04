from flask.views import MethodView
from flask import request
from flask_smorest import Blueprint, abort

from models.owner import OwnerModel
from schemas.owner import OwnerListItemSchema

blp = Blueprint("Owners", __name__, description="Owner profiles")


@blp.route("/owners")
class OwnersList(MethodView):

    @blp.response(200, OwnerListItemSchema(many=True))
    def get(self):
        q = (request.args.get("q") or request.args.get("search") or "").strip()
        if len(q) < 2:
            return []

        owners = OwnerModel.query.filter(
            OwnerModel.name.ilike(f"%{q}%")
        ).limit(10).all()

        return [{"id": o.id, "name": o.name} for o in owners]
