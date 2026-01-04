# SafePaws

## Overview
SafePaws is a two-sided pet boarding platform specifically designed for the Tunisian market. Its mission is to provide "A safe home for every pet" by connecting pet owners with trusted care providers.

## Tech Stack
- **Framework**: Flask 3.x with Flask-Smorest for REST API
- **Database**: SQLite (petboarding.db in instance folder)
- **Authentication**: JWT via Flask-JWT-Extended
- **Frontend**: Plain HTML/CSS with Jinja2 templates, Leaflet.js for maps.

Maps integration (optional): Add a Maps Pro provider by setting the following environment variables: `MAPS_PRO_URL` (reverse geocode endpoint) and `MAPS_PRO_KEY`. If not set, a free fallback using OpenStreetMap's Nominatim is used for reverse geocoding.

Database migration: after pulling changes, run `python scripts/add_service_geo.py` to add `geocoded_name`, `latitude`, and `longitude` columns to the `boarding_services` table (SQLite support).
- **Documentation**: OpenAPI 3.0 / Swagger UI at `/swagger-ui`

## Branding
- **Name**: SafePaws
- **Tagline**: A safe home for every pet.
- **Colors**: Warm Orange, Sand, Soft Blue.

## Project Structure
```

## Messaging

- **Owner ↔ Provider**: 1:1 conversations with messages stored in `messages` and `conversations` tables; API endpoints at `/conversations` and `/conversations/<id>/messages`.
- **Community**: Shared owners-only chat room at `/chat/rooms/owners`, UI at `/community` and endpoints at `/chat/rooms` and `/chat/rooms/<id>/messages`.
├── app.py              # Application factory and entry point
├── templates/          # Jinja2 HTML templates
│   ├── index.html      # Rebranded SafePaws landing page
│   ├── find_care.html  # Pet owner journey
│   └── offer_care.html # Provider journey
├── static/
│   ├── images/         # Brand assets and backgrounds
│   └── css/            # Global styles
```