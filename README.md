# Task Management API

A production-ready REST API for managing users and tasks built with FastAPI, PostgreSQL, SQLAlchemy 2.0, and Alembic.

The project follows a layered architecture with clean separation between API routes, services, database models, and migrations.

## Tech Stack

- Python 3.12+
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy 2.0 (Async)
- AsyncPG
- Alembic (Database migrations)
- Pydantic v2
- Pydantic Settings
- UV (Package Manager)

---

## Features

- User management
- Task CRUD operations
- Async database operations
- PostgreSQL integration
- SQLAlchemy ORM models
- Database migrations using Alembic
- Environment based configuration
- Request validation using Pydantic
- Structured API error handling
- Automatic OpenAPI documentation

---

## Project Structure

fastapi-task-app/

├── app/
│ ├── api/
│ │ ├── routes/
│ │ └── dependencies/
│ │
│ ├── core/
│ │ ├── config.py
│ │ └── exceptions.py
│ │
│ ├── db/
│ │ ├── models/
│ │ ├── base.py
│ │ └── session.py
│ │
│ ├── schemas/
│ │
│ ├── services/
│ │
│ └── main.py
│
├── migrations/
│ └── versions/
│
├── alembic.ini
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md

---

# Getting Started

## Requirements

Install:

- Python 3.12+
- PostgreSQL
- UV

Check versions:

```bash
python --version

uv --version

psql --version
Installation

Clone the repository:

git clone <repository-url>

cd fastapi-task-app
Install Dependencies

Using UV:

uv sync

This will install all dependencies from:

pyproject.toml
uv.lock
Environment Configuration

Create a .env file:

DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/task_db

Example:

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/task_db
Database Setup

Create PostgreSQL database:

CREATE DATABASE task_db;
Database Migrations

This project uses Alembic for schema migrations.

Apply migrations

Run:

uv run alembic upgrade head
Create a new migration

After changing SQLAlchemy models:

uv run alembic revision --autogenerate -m "your migration message"

Example:

uv run alembic revision --autogenerate -m "add task table"
Check current migration
uv run alembic current
Running Application
Development

Start server:

uv run uvicorn app.main:app --reload

Server:

http://localhost:8000
Production

Run with multiple workers:

uv run uvicorn app.main:app \
--host 0.0.0.0 \
--port 8000 \
--workers 4
API Documentation

FastAPI automatically generates API documentation.

Swagger:

http://localhost:8000/docs

ReDoc:

http://localhost:8000/redoc
API Examples
Create User

Endpoint:

POST /users

Request:

{
    "email": "john@example.com",
    "name": "John"
}

Response:

{
    "id": "uuid",
    "email": "john@example.com",
    "name": "John"
}
Find User By Email

Endpoint:

GET /users/find-by-email?email=john@example.com
Create Task

Endpoint:

POST /tasks

Request:

{
    "name": "Build API",
    "description": "Create FastAPI backend",
    "priority": "HIGH",
    "status": "NOT_STARTED"
}
Get Tasks

Endpoint:

GET /tasks

Response:

{
    "count": 2,
    "data": [
        {
            "id": "uuid",
            "name": "Build API"
        }
    ]
}
Response Format
Success Responses

Single resource:

{
    "id": "uuid",
    "name": "Task"
}

List response:

{
    "count": 10,
    "data": []
}
Error Responses

Errors follow a standard format:

{
    "type": "/errors/not-found",
    "title": "Resource not found",
    "status": 404,
    "traceId": "uuid",
    "detail": "User does not exist",
    "instance": "/users/123"
}
Development Workflow

When adding a new feature:

Create/update SQLAlchemy model
Add schema
Add service logic
Add API route
Generate migration:
uv run alembic revision --autogenerate -m "feature name"
Apply migration:
uv run alembic upgrade head
Run application:
uv run uvicorn app.main:app --reload
Useful Commands

Install package:

uv add package-name

Remove package:

uv remove package-name

Sync dependencies:

uv sync

Run Python:

uv run python
Environment Variables
Variable	Description
DATABASE_URL	PostgreSQL database connection
ENVIRONMENT	Application environment
SECRET_KEY	Application secret
Git Rules

Do not commit:

.env
.venv/
__pycache__/
*.pyc

Commit:

pyproject.toml
uv.lock
migrations/
Future Improvements

Possible improvements:

Docker support
CI/CD pipeline
JWT authentication
Role-based access control
Redis caching
Background jobs
Test coverage
Deployment configuration
License

MIT License
```
