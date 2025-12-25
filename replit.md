# Pet Boarding REST API

## Overview
A Flask-based REST API for managing pet boarding services. Features include owner/provider authentication, pet management, service offerings, and reservation handling.

## Tech Stack
- **Framework**: Flask 3.x with Flask-Smorest for REST API
- **Database**: SQLite (petboarding.db in instance folder)
- **Authentication**: JWT via Flask-JWT-Extended
- **Documentation**: OpenAPI 3.0 / Swagger UI at `/swagger-ui`

## Project Structure
```
├── app.py              # Application factory and entry point
├── db.py               # SQLAlchemy database instance
├── models/             # SQLAlchemy ORM models
│   ├── owner.py
│   ├── pet.py
│   ├── provider.py
│   ├── reservation.py
│   └── service.py
├── resources/          # API blueprints/endpoints
│   ├── auth.py         # Owner/Provider authentication
│   ├── pets.py         # Pet CRUD operations
│   ├── reservations.py # Booking management
│   └── services.py     # Service offerings
├── schemas/            # Marshmallow schemas for serialization
└── instance/           # SQLite database storage
```

## Running the Application
The API runs on port 5000 and is accessible via the Swagger UI at `/swagger-ui`.

## API Endpoints
- **Auth**: `/owner/register`, `/owner/login`, `/provider/register`, `/provider/login`
- **Pets**: `/pets` (GET, POST), `/pets/{pet_id}` (DELETE)
- **Services**: Service management endpoints
- **Reservations**: Booking management endpoints
