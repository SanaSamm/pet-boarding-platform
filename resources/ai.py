from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
import os
import requests

from db import db
from models.service import BoardingServiceModel
from models.review import ReviewModel
from schemas.ai import ConciergeRequestSchema, ConciergeResponseSchema
from resources.services import _haversine_km
from sqlalchemy import func, Text, cast, or_


blp = Blueprint("AI", __name__, description="AI concierge helpers")

_CITY_KEYWORDS = [
    "tunis", "ariana", "ben arous", "manouba", "sousse", "sfax", "bizerte",
    "nabeul", "monastir", "kairouan", "gabes", "gafsa", "tataouine",
    "medenine", "mahdia", "beja", "jendouba", "kef", "kasserine",
    "siliana", "zaghouan", "tozeur", "kebili", "ain zaghouan",
]

_SERVICE_KEYWORDS = {
    "grooming": ["grooming", "spa", "shower", "bath", "wash"],
    "walking": ["walking", "walk", "walks", "daily walks", "dog walk"],
    "boarding": ["boarding", "overnight", "stay"],
    "daycare": ["daycare", "day care", "day-care"],
    "training": ["training", "trainer"],
    "vet": ["vet", "clinic", "medical"],
}

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


def _aiml_chat(prompt, max_tokens, temperature):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.2")
    site_url = os.getenv("OPENROUTER_SITE_URL")
    site_title = os.getenv("OPENROUTER_SITE_TITLE")
    url = base_url.rstrip("/") + "/chat/completions"

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if site_url:
            headers["HTTP-Referer"] = site_url
        if site_title:
            headers["X-Title"] = site_title

        resp = requests.post(
            url,
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=15,
        )
        if not resp.ok:
            print(f"OpenRouter API error {resp.status_code}: {resp.text}")
            return None
        data = resp.json()
        choices = data.get("choices") if isinstance(data, dict) else None
        if choices and isinstance(choices, list):
            message = choices[0].get("message") or {}
            text = message.get("content")
            return text.strip() if text else None
    except Exception as exc:
        print(f"OpenRouter API request failed: {exc}")
        return None

    return None


def _llm_answer(query_text, matches):
    lines = []
    for m in matches[:5]:
        price = m.get("price_per_day")
        price_str = f"{price} TND/day" if price is not None else "price on request"
        loc = m.get("location") or ""
        lines.append(f"- {m.get('name')} ({loc}) - {price_str}")

    listing = "\n".join(lines) if lines else "No matching services found."
    prompt = (
        "You are SafePaws AI concierge. Greet briefly and help the user.\n"
        f"User query: {query_text}\n"
        "Available services:\n"
        f"{listing}\n"
        "Respond with a short helpful answer and ask one follow-up question.\n"
        "If no matches, suggest changing location, price, or service type.\n"
    )

    return _aiml_chat(prompt, max_tokens=180, temperature=0.2)


def _llm_general_answer(query_text):
    prompt = (
        "You are SafePaws AI assistant. Answer user questions about the pet boarding platform, "
        "booking flow, pricing basics, reviews, messaging, and how to use the app. "
        "If unsure, ask a clarifying question. Keep it short and helpful.\n"
        f"User query: {query_text}\n"
        "Answer:\n"
    )

    return _aiml_chat(prompt, max_tokens=160, temperature=0.3)


def _extract_city(text):
    lower = text.lower()
    for city in _CITY_KEYWORDS:
        if city in lower:
            return city.title()
    return None


def _extract_service_keyword(text):
    lower = text.lower()
    for key, variants in _SERVICE_KEYWORDS.items():
        for v in variants:
            if v in lower:
                return key, variants
    return None, None


def _extract_max_price(text):
    # Find numbers and pick the last one as max price (simple heuristic)
    nums = []
    current = ""
    for ch in text:
        if ch.isdigit():
            current += ch
        elif current:
            nums.append(current)
            current = ""
    if current:
        nums.append(current)
    if not nums:
        return None
    try:
        return float(nums[-1])
    except ValueError:
        return None


@blp.route("/ai/concierge")
class Concierge(MethodView):
    """Rule-based concierge that searches services using natural language."""

    @blp.arguments(ConciergeRequestSchema)
    @blp.response(200, ConciergeResponseSchema)
    def post(self, data):
        query_text = (data.get("query") or "").strip()
        if not query_text:
            abort(400, message="query is required")

        city = data.get("location") or _extract_city(query_text)
        keyword, keyword_variants = _extract_service_keyword(query_text)
        if data.get("service_keyword"):
            keyword = data.get("service_keyword")
            keyword_variants = [keyword]
        max_price = data.get("max_price")
        if max_price is None:
            max_price = _extract_max_price(query_text)

        lat = data.get("lat")
        lng = data.get("lng") or data.get("lon")

        def build_query(with_city=True):
            q = BoardingServiceModel.query.filter(BoardingServiceModel.is_deleted == False)
            if with_city and city:
                q = q.filter(BoardingServiceModel.location.ilike(f"%{city}%"))
            if keyword_variants:
                ors = []
                for v in keyword_variants:
                    kw = f"%{v.lower()}%"
                    ors.append(func.lower(BoardingServiceModel.type).like(kw))
                    ors.append(func.lower(BoardingServiceModel.name).like(kw))
                    ors.append(func.lower(BoardingServiceModel.description).like(kw))
                    ors.append(func.lower(cast(BoardingServiceModel.services_provided, Text)).like(kw))
                q = q.filter(or_(*ors))
            if max_price is not None:
                try:
                    mp = float(max_price)
                    q = q.filter(
                        BoardingServiceModel.price_per_day.isnot(None),
                        BoardingServiceModel.price_per_day <= mp
                    )
                except ValueError:
                    abort(400, message="max_price must be a number")
            return q

        has_service_intent = bool(keyword_variants or city or max_price is not None)

        results = []
        expanded_search = False
        if has_service_intent:
            results = build_query(with_city=True).limit(8).all()
            if not results and city:
                results = build_query(with_city=False).limit(8).all()
                expanded_search = True

        # Distance sorting if coordinates provided
        if lat is not None and lng is not None:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
                for s in results:
                    if s.latitude is not None and s.longitude is not None:
                        s.distance_km = _haversine_km(lat_f, lng_f, s.latitude, s.longitude)
                    else:
                        s.distance_km = None
                results.sort(key=lambda x: x.distance_km if x.distance_km is not None else 1e9)
            except ValueError:
                pass

        provider_ids = [s.provider_id for s in results if s.provider_id is not None]
        services_by_provider = {}
        if provider_ids:
            svc_rows = BoardingServiceModel.query.filter(BoardingServiceModel.provider_id.in_(provider_ids)).all()
            for svc in svc_rows:
                services_by_provider.setdefault(svc.provider_id, []).append(svc)

        avg_rows = db.session.query(
            ReviewModel.provider_id,
            func.avg(ReviewModel.rating).label("avg_rating"),
            func.count(ReviewModel.id).label("review_count"),
        ).filter(ReviewModel.provider_id.in_(provider_ids)).group_by(ReviewModel.provider_id).all() if provider_ids else []
        avg_map = {row.provider_id: float(row.avg_rating) for row in avg_rows if row.avg_rating is not None}
        count_map = {row.provider_id: int(row.review_count) for row in avg_rows}

        payload = []
        for s in results:
            highlights = _build_highlights(
                services_by_provider.get(s.provider_id, []),
                avg_map.get(s.provider_id),
                count_map.get(s.provider_id),
            )
            payload.append({
                "id": s.id,
                "name": s.name,
                "location": s.location,
                "price_per_day": s.price_per_day,
                "provider_id": s.provider_id,
                "services_provided": s.services_provided or [],
                "distance_km": getattr(s, "distance_km", None),
                "highlights": highlights,
            })

        llm_used = False
        if has_service_intent:
            answer = "I found {} matching providers.".format(len(payload))
            if keyword:
                answer = "I found {} providers offering {}.".format(len(payload), keyword)
            llm = _llm_answer(query_text, payload)
            if llm:
                answer = llm
                llm_used = True
        else:
            llm = _llm_general_answer(query_text)
            if llm:
                answer = llm
                llm_used = True
            else:
                answer = "Hi! How can I help you with pet care today?"
        note = None
        if expanded_search:
            note = "No exact matches in {}. Showing providers outside that city.".format(city)

        return {
            "query": query_text,
            "interpreted": {"location": city, "service_keyword": keyword, "max_price": max_price, "expanded_search": expanded_search},
            "answer": answer,
            "mode": "service" if has_service_intent else "general",
            "llm_used": llm_used,
            "note": note,
            "results": payload,
        }
