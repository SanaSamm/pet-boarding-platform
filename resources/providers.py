from flask.views import MethodView
from flask import request
from sqlalchemy import func
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from db import db
from models.provider import ProviderModel
from models.service import BoardingServiceModel
from models.review import ReviewModel
from schemas.provider import ProviderProfileSchema, ProviderUpdateSchema, ProviderListItemSchema

blp = Blueprint("Providers", __name__, description="Provider profiles")

def _build_highlights(services, avg_rating, review_count):
    top_services = []
    for s in services:
        for item in (s.services_provided or []):
            if item and item not in top_services:
                top_services.append(item)
        if len(top_services) >= 3:
            break

    price_vals = [s.price_per_day for s in services if s.price_per_day is not None]
    min_price = min(price_vals) if price_vals else None

    parts = []
    if top_services:
        parts.append("Top services: " + ", ".join(top_services[:3]))
    if avg_rating is not None and review_count is not None:
        parts.append(f"Rating {avg_rating:.1f} ({review_count} reviews)")
    elif avg_rating is not None:
        parts.append(f"Rating {avg_rating:.1f}")
    if min_price is not None:
        parts.append(f"From {min_price:g} TND/day")

    return " | ".join(parts) if parts else None

@blp.route("/providers")
class ProvidersList(MethodView):

    @blp.response(200, ProviderListItemSchema(many=True))
    def get(self):
        q = (request.args.get("q") or request.args.get("search") or "").strip()
        query = ProviderModel.query
        has_paging = "page" in request.args or "per_page" in request.args
        if len(q) >= 2:
            query = query.filter(ProviderModel.name.ilike(f"%{q}%"))
        elif not has_paging:
            return []

        sort_by = (request.args.get("sort_by") or "name").strip()
        order = (request.args.get("order") or "asc").lower()
        avg_subq = None
        if sort_by == "rating":
            avg_subq = db.session.query(
                ReviewModel.provider_id,
                func.avg(ReviewModel.rating).label("avg_rating"),
            ).group_by(ReviewModel.provider_id).subquery()
            query = query.outerjoin(avg_subq, ProviderModel.id == avg_subq.c.provider_id)
            rating_col = func.coalesce(avg_subq.c.avg_rating, 0)
            if order == "desc":
                query = query.order_by(rating_col.desc(), ProviderModel.name.asc())
            else:
                query = query.order_by(rating_col.asc(), ProviderModel.name.asc())
        else:
            sort_map = {
                "name": ProviderModel.name,
                "id": ProviderModel.id,
            }
            col = sort_map.get(sort_by, ProviderModel.name)
            query = query.order_by(col.desc() if order == "desc" else col.asc())

        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 20))
        except ValueError:
            abort(400, message="page and per_page must be integers")
        if page < 1 or per_page < 1 or per_page > 100:
            abort(400, message="page must be >= 1 and per_page between 1 and 100")

        if not has_paging and len(q) >= 2:
            providers = query.limit(10).all()
        else:
            providers = query.offset((page - 1) * per_page).limit(per_page).all()

        avg_map = {}
        count_map = {}
        if avg_subq is None:
            avg_rows = db.session.query(
                ReviewModel.provider_id,
                func.avg(ReviewModel.rating).label("avg_rating"),
                func.count(ReviewModel.id).label("review_count"),
            ).group_by(ReviewModel.provider_id).all()
            avg_map = {row.provider_id: float(row.avg_rating) for row in avg_rows if row.avg_rating is not None}
            count_map = {row.provider_id: int(row.review_count) for row in avg_rows}
        else:
            avg_rows = db.session.query(
                ReviewModel.provider_id,
                func.avg(ReviewModel.rating).label("avg_rating"),
                func.count(ReviewModel.id).label("review_count"),
            ).group_by(ReviewModel.provider_id).all()
            avg_map = {row.provider_id: float(row.avg_rating) for row in avg_rows if row.avg_rating is not None}
            count_map = {row.provider_id: int(row.review_count) for row in avg_rows}

        provider_ids = [p.id for p in providers]
        services_by_provider = {}
        if provider_ids:
            svc_rows = BoardingServiceModel.query.filter(BoardingServiceModel.provider_id.in_(provider_ids)).all()
            for svc in svc_rows:
                services_by_provider.setdefault(svc.provider_id, []).append(svc)

        return [
            {
                "id": p.id,
                "name": p.name,
                "bio": p.bio,
                "photo_url": p.photo_url,
                "average_rating": avg_map.get(p.id),
                "highlights": _build_highlights(
                    services_by_provider.get(p.id, []),
                    avg_map.get(p.id),
                    count_map.get(p.id)
                ),
            }
            for p in providers
        ]


@blp.route("/providers/<int:provider_id>")
class ProviderResource(MethodView):

    @blp.response(200, ProviderProfileSchema)
    def get(self, provider_id):
        provider = ProviderModel.query.get_or_404(provider_id)

        services = BoardingServiceModel.query.filter(BoardingServiceModel.provider_id == provider_id).all()
        services_list = []
        for s in services:
            # Sanity: only include services where provider_id matches (defensive)
            if s.provider_id != provider_id:
                continue
            services_list.append({"id": s.id, "name": s.name, "price_per_day": s.price_per_day, "provider_id": s.provider_id, "services_provided": s.services_provided or []})

        reviews = ReviewModel.query.filter_by(provider_id=provider_id).all()
        avg = None
        if reviews:
            avg = sum(r.rating for r in reviews) / len(reviews)

        # Try provider-level services_offered first, otherwise compute from services
        provided = provider.services_offered or []
        if not provided:
            seen = set()
            for s in services:
                if not s.services_provided:
                    continue
                for item in s.services_provided:
                    if item and item not in seen:
                        seen.add(item)
            provided = sorted(seen)

        return {
            "id": provider.id,
            "name": provider.name,
            "bio": provider.bio,
            "photo_url": provider.photo_url,
            "average_rating": avg,
            "services": services_list,
            "provided_services": provided,
            "highlights": _build_highlights(services, avg, len(reviews)),
        }

    @jwt_required()
    @blp.arguments(ProviderUpdateSchema)
    @blp.response(200, ProviderProfileSchema)
    def put(self, update_data, provider_id):
        # Only providers may update their own profile
        claims = get_jwt()
        if claims.get("role") != "provider":
            abort(403, message="Only providers can edit their profile")

        provider_id_auth = int(get_jwt_identity())
        if provider_id_auth != provider_id:
            abort(403, message="You can only edit your own profile")

        provider = ProviderModel.query.get_or_404(provider_id)
        provider.bio = update_data.get("bio")
        provider.photo_url = update_data.get("photo_url")

        # Accept provider-level services_offered update
        offered = update_data.get('services_offered')
        if offered is not None:
            # ensure it's a list (client may send comma separated string or list)
            if isinstance(offered, str):
                offered_list = [s.strip() for s in offered.split(',') if s.strip()]
            elif isinstance(offered, list):
                offered_list = [s for s in offered if s]
            else:
                offered_list = []
            provider.services_offered = offered_list

        db.session.commit()

        # Recompute services and avg to return full profile
        services = BoardingServiceModel.query.filter_by(provider_id=provider_id).all()
        services_list = [{"id": s.id, "name": s.name, "price_per_day": s.price_per_day, "services_provided": s.services_provided or []} for s in services]
        reviews = ReviewModel.query.filter_by(provider_id=provider_id).all()
        avg = None
        if reviews:
            avg = sum(r.rating for r in reviews) / len(reviews)

        # recompute provided list from provider.services_offered or services
        provided = provider.services_offered or []
        if not provided:
            seen = set()
            for s in services:
                if not s.services_provided:
                    continue
                for item in s.services_provided:
                    if item and item not in seen:
                        seen.add(item)
            provided = sorted(seen)

        return {
            "id": provider.id,
            "name": provider.name,
            "bio": provider.bio,
            "photo_url": provider.photo_url,
            "average_rating": avg,
            "services": services_list,
            "provided_services": provided,
        }
