# Safepaws

## Overview
Safepaws is a two-sided pet boarding platform specifically designed for the Tunisian market. Its mission is to provide "A safe home for every pet" by connecting pet owners with trusted care providers.

## Tech Stack
- **Framework**: Flask 3.x with Flask-Smorest for REST API
- **Database**: SQLite (petboarding.db in instance folder)
- **Authentication**: JWT via Flask-JWT-Extended
- **Frontend**: Plain HTML/CSS with Jinja2 templates, Leaflet.js for maps.
- **Documentation**: OpenAPI 3.0 / Swagger UI at `/swagger-ui`

## Branding
- **Name**: Safepaws
- **Tagline**: A safe home for every pet.
- **Colors**: Warm Orange, Sand, Soft Blue.

## Project Structure
```
├── app.py              # Application factory and entry point
├── templates/          # Jinja2 HTML templates
│   ├── index.html      # Rebranded Safepaws landing page
│   ├── find_care.html  # Pet owner journey
│   └── offer_care.html # Provider journey
├── static/
│   ├── images/         # Brand assets and backgrounds
│   └── css/            # Global styles
```