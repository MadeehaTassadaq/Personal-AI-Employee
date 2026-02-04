---
name: fastapi
description: Comprehensive FastAPI backend development skill for building modern Python REST APIs. Use when creating new FastAPI projects, adding API endpoints, implementing authentication, integrating databases, or working with any FastAPI-related backend development tasks. Triggers include mentions of FastAPI, building APIs with Python, REST API development, backend services, or API documentation.
---

# FastAPI Backend Development

## Overview

This skill provides comprehensive guidance for building production-ready REST APIs with FastAPI, including project initialization, database integration, authentication, testing, and deployment best practices.

## Quick Start

### Initialize New Project

Use the project initialization script to create a new FastAPI project with recommended structure:

```bash
python scripts/init_project.py <project-name> [--database sqlalchemy|none] [--auth]
```

Examples:
```bash
# Basic project
python scripts/init_project.py my-api

# With PostgreSQL and authentication
python scripts/init_project.py my-api --database sqlalchemy --auth
```

The script creates:
- Complete project structure with proper organization
- Configuration management with environment variables
- Docker setup for containerization
- Basic CRUD example endpoints
- Testing setup with pytest
- Database migrations (if using database)
- Authentication scaffolding (if using --auth)

## Core Capabilities

### 1. Project Structure and Organization

Follow the recommended project structure for maintainability:

```
project/
├── app/
│   ├── main.py              # Application entry point
│   ├── api/                 # API routes
│   │   └── v1/             # API versioning
│   ├── core/                # Core functionality
│   │   ├── config.py       # Configuration
│   │   ├── security.py     # Auth utilities
│   │   └── database.py     # Database setup
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── crud/                # CRUD operations
│   └── services/            # Business logic
├── tests/                   # Test files
└── alembic/                 # Database migrations
```

**See [best-practices.md](references/best-practices.md) for detailed project structure guidance.**

### 2. Building API Endpoints

FastAPI uses path operations with automatic validation and documentation:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

@app.post("/items", status_code=201)
async def create_item(item: Item):
    """Create a new item."""
    return {"id": 1, **item.dict()}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """Get item by ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]
```

**Key concepts:**
- Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- Define Pydantic models for request/response validation
- Set proper status codes (201 for created, 404 for not found, etc.)
- Use path and query parameters with automatic type conversion

**See [core-concepts.md](references/core-concepts.md) for comprehensive endpoint patterns.**

### 3. Database Integration

FastAPI works seamlessly with SQLAlchemy for database operations:

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from app.core.database import Base, get_db

# Define model
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

# Use in endpoint
@app.get("/items")
def read_items(db: Session = Depends(get_db)):
    """List all items."""
    return db.query(Item).all()
```

**Database workflow:**
1. Define SQLAlchemy models in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement CRUD operations in `app/crud/`
4. Use dependency injection for database sessions
5. Generate and apply migrations with Alembic

**See [database.md](references/database.md) for setup, relationships, async operations, and migrations.**

### 4. Authentication and Security

Implement JWT-based authentication for protected endpoints:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate token and return current user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401)
        return get_user(username)
    except JWTError:
        raise HTTPException(status_code=401)

@app.get("/users/me")
async def read_users_me(current_user = Depends(get_current_user)):
    """Get current user info (protected)."""
    return current_user
```

**Authentication patterns:**
- JWT tokens with access/refresh mechanism
- OAuth2 password flow
- API key authentication
- Session-based authentication

**See [authentication.md](references/authentication.md) for complete auth implementation patterns.**

### 5. Testing

Use pytest and TestClient for comprehensive testing:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_item():
    """Test item creation."""
    response = client.post(
        "/items",
        json={"name": "Test Item", "price": 10.99}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"

def test_read_item_not_found():
    """Test 404 error."""
    response = client.get("/items/999")
    assert response.status_code == 404
```

**Testing strategy:**
- Test all endpoints (success and error cases)
- Use fixtures for database setup
- Mock external dependencies
- Test authentication flows
- Aim for >80% code coverage

**See [testing.md](references/testing.md) for fixtures, async testing, and mocking patterns.**

## Common Workflows

### Create a New API Endpoint

1. **Define Pydantic schema** in `app/schemas/`:
```python
class ItemCreate(BaseModel):
    name: str
    price: float
```

2. **Create database model** (if needed) in `app/models/`:
```python
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

3. **Implement CRUD function** in `app/crud/`:
```python
def create_item(db: Session, item: ItemCreate):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    return db_item
```

4. **Add route** in `app/api/v1/endpoints/`:
```python
@router.post("/items", status_code=201)
def create_item_endpoint(item: ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)
```

5. **Write tests** in `tests/`:
```python
def test_create_item(client):
    response = client.post("/items", json={"name": "Test", "price": 10})
    assert response.status_code == 201
```

### Add Authentication to Existing Project

1. Install dependencies: `pip install python-jose[cryptography] passlib[bcrypt]`
2. See [authentication.md](references/authentication.md) for complete implementation
3. Create auth utilities in `app/core/security.py`
4. Add login endpoint returning JWT token
5. Protect routes using `Depends(get_current_user)`

### Integrate Database

1. Install SQLAlchemy: `pip install sqlalchemy alembic psycopg2-binary`
2. Configure database in `app/core/database.py`
3. Define models in `app/models/`
4. Initialize Alembic: `alembic init alembic`
5. Generate migration: `alembic revision --autogenerate -m "Initial"`
6. Apply migration: `alembic upgrade head`

See [database.md](references/database.md) for detailed setup.

## Reference Documentation

This skill includes comprehensive reference documentation:

- **[core-concepts.md](references/core-concepts.md)** - Path operations, dependency injection, validation, response models
- **[database.md](references/database.md)** - SQLAlchemy setup, models, relationships, CRUD, async operations, migrations
- **[authentication.md](references/authentication.md)** - JWT, OAuth2, API keys, sessions, security best practices
- **[testing.md](references/testing.md)** - Test setup, fixtures, mocking, async testing, coverage
- **[best-practices.md](references/best-practices.md)** - Project structure, error handling, performance, API design

Load these references when you need detailed information about specific topics.

## Development Workflow

1. **Initialize project** with `scripts/init_project.py`
2. **Define data models** and schemas
3. **Implement API endpoints** with proper validation
4. **Add authentication** if needed
5. **Write tests** for all endpoints
6. **Document endpoints** (automatic via FastAPI)
7. **Run locally** with `uvicorn app.main:app --reload`
8. **Test** with `pytest`
9. **Deploy** using Docker or cloud platform

## Automatic Documentation

FastAPI generates interactive API documentation automatically:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

The documentation updates automatically based on your code, including:
- All endpoints and HTTP methods
- Request/response schemas
- Validation requirements
- Authentication flows

## Best Practices Summary

- ✓ Separate concerns (routes, models, schemas, CRUD, services)
- ✓ Use type hints everywhere for automatic validation
- ✓ Implement proper error handling with custom exceptions
- ✓ Use async for I/O-bound operations
- ✓ Apply authentication and rate limiting
- ✓ Write comprehensive tests (>80% coverage)
- ✓ Use environment variables for configuration
- ✓ Follow RESTful conventions
- ✓ Version your API (e.g., /api/v1/)
- ✓ Document with clear docstrings

See [best-practices.md](references/best-practices.md) for detailed guidelines.
