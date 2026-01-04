from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from db import db
from models.review import ReviewModel
from models.provider import ProviderModel
from schemas.review import ReviewSchema

blp = Blueprint("Reviews", __name__, description="Provider reviews")


@blp.route("/providers/<int:provider_id>/reviews")
class ProviderReviews(MethodView):

    @blp.response(200, ReviewSchema(many=True))
    def get(self, provider_id):
        ProviderModel.query.get_or_404(provider_id)
        reviews = ReviewModel.query.filter_by(provider_id=provider_id).all()

        # Enrich reviews with reviewer_name for frontend convenience
        out = []
        for r in reviews:
            rev = r.__dict__.copy()
            reviewer_name = None
            if r.reviewer_role == 'owner' and r.reviewer_id:
                from models.owner import OwnerModel
                owner = OwnerModel.query.get(r.reviewer_id)
                reviewer_name = owner.name if owner else None
            elif r.reviewer_role == 'provider' and r.reviewer_id:
                from models.provider import ProviderModel as Prov
                prov = Prov.query.get(r.reviewer_id)
                reviewer_name = prov.name if prov else None
            else:
                # fallback: legacy owner_id
                if r.owner_id:
                    from models.owner import OwnerModel
                    owner = OwnerModel.query.get(r.owner_id)
                    reviewer_name = owner.name if owner else None

            out.append({
                'id': r.id,
                'reviewer_role': r.reviewer_role or ('owner' if r.owner_id else None),
                'reviewer_id': r.reviewer_id or r.owner_id,
                'reviewer_name': reviewer_name,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at,
            })
        return out

    @jwt_required()
    @blp.arguments(ReviewSchema)
    @blp.response(201, ReviewSchema)
    def post(self, review_data, provider_id):
        claims = get_jwt()
        role = claims.get('role')
        if role not in ('owner', 'provider'):
            abort(403, message="Only owners or providers can leave reviews")

        reviewer_id = int(get_jwt_identity())
        ProviderModel.query.get_or_404(provider_id)

        # Providers cannot review their own profile
        if role == 'provider' and reviewer_id == provider_id:
            abort(403, message="You cannot review your own profile")

        review = ReviewModel(
            provider_id=provider_id,
            rating=review_data["rating"],
            comment=review_data.get("comment"),
            reviewer_role=role,
            reviewer_id=reviewer_id
        )

        # For backward-compat, set owner_id for owner reviewers
        if role == 'owner':
            review.owner_id = reviewer_id

        db.session.add(review)
        db.session.commit()
        # Enrich response similar to GET
        reviewer_name = None
        if role == 'owner':
            from models.owner import OwnerModel
            o = OwnerModel.query.get(reviewer_id)
            reviewer_name = o.name if o else None
        else:
            from models.provider import ProviderModel as Prov
            p = Prov.query.get(reviewer_id)
            reviewer_name = p.name if p else None

        return {
            'id': review.id,
            'reviewer_role': review.reviewer_role,
            'reviewer_id': review.reviewer_id,
            'reviewer_name': reviewer_name,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at,
        }
