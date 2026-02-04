# FastAPI Best Practices

## Table of Contents
- [Project Structure](#project-structure)
- [Code Organization](#code-organization)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Security](#security)
- [API Design](#api-design)
- [Documentation](#documentation)

## Project Structure

### Recommended Structure
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── deps.py             # Shared dependencies
│   │   └── v1/                 # API version
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── items.py
│   │       │   └── users.py
│   │       └── router.py       # Version router
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration
│   │   ├── security.py         # Auth utilities
│   │   └── database.py         # Database setup
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   ├── crud/                   # CRUD operations
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   └── services/               # Business logic
│       ├── __init__.py
│       └── email.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_api/
├── alembic/                    # Database migrations
├── .env
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### Separation of Concerns
- **main.py**: Application initialization, middleware, CORS
- **api/**: Route definitions only
- **crud/**: Database operations
- **schemas/**: Request/response validation
- **models/**: Database models
- **services/**: Business logic
- **core/**: Configuration, security, utilities

## Code Organization

### Router Organization
```python
# app/api/v1/endpoints/items.py
from fastapi import APIRouter, Depends
from app.schemas.item import Item, ItemCreate
from app.crud import item as item_crud
from app.api.deps import get_db

router = APIRouter()

@router.get("/", response_model=list[Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List items."""
    return item_crud.get_items(db, skip=skip, limit=limit)

@router.post("/", response_model=Item, status_code=201)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create new item."""
    return item_crud.create_item(db, item)
```

### CRUD Layer
```python
# app/crud/item.py
from sqlalchemy.orm import Session
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate

def get_item(db: Session, item_id: int) -> Item | None:
    """Get item by ID."""
    return db.query(Item).filter(Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100) -> list[Item]:
    """Get list of items."""
    return db.query(Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: ItemCreate) -> Item:
    """Create new item."""
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, item_id: int, item: ItemUpdate) -> Item | None:
    """Update item."""
    db_item = get_item(db, item_id)
    if not db_item:
        return None
    update_data = item.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
    return db_item
```

### Schema Organization
```python
# app/schemas/item.py
from pydantic import BaseModel, Field
from datetime import datetime

class ItemBase(BaseModel):
    """Base item schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(..., gt=0)

class ItemCreate(ItemBase):
    """Schema for creating items."""
    pass

class ItemUpdate(ItemBase):
    """Schema for updating items."""
    name: str | None = None
    price: float | None = None

class Item(ItemBase):
    """Schema for item responses."""
    id: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
```

## Error Handling

### Custom Exception Handlers
```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

class ItemNotFoundException(Exception):
    """Custom exception for item not found."""
    def __init__(self, item_id: int):
        self.item_id = item_id

@app.exception_handler(ItemNotFoundException)
async def item_not_found_handler(request: Request, exc: ItemNotFoundException):
    """Handle item not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Item {exc.item_id} not found"}
    )
```

### Error Response Models
```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: list[dict]
    error_code: str = "VALIDATION_ERROR"

@app.get("/items/{item_id}",
         responses={
             404: {"model": ErrorResponse, "description": "Item not found"},
             422: {"model": ValidationErrorResponse, "description": "Validation error"}
         })
def read_item(item_id: int):
    """Get item with documented errors."""
    pass
```

## Performance Optimization

### Use Async When Appropriate
```python
# Use async for I/O-bound operations
@app.get("/external-data")
async def get_external_data():
    """Fetch data from external API."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
    return response.json()

# Use sync for CPU-bound operations
@app.post("/process")
def process_data(data: list[int]):
    """CPU-intensive processing."""
    return {"result": sum(data)}
```

### Database Query Optimization
```python
from sqlalchemy.orm import joinedload

# Eager loading to avoid N+1 queries
def get_users_with_items(db: Session):
    """Get users with their items."""
    return db.query(User).options(joinedload(User.items)).all()

# Pagination
def get_items_paginated(db: Session, page: int = 1, page_size: int = 20):
    """Get paginated items."""
    return db.query(Item).offset((page - 1) * page_size).limit(page_size).all()

# Select specific columns
def get_item_names(db: Session):
    """Get only item names."""
    return db.query(Item.id, Item.name).all()
```

### Caching
```python
from functools import lru_cache
from fastapi import Depends

@lru_cache()
def get_settings():
    """Cache settings (singleton pattern)."""
    return Settings()

# Redis caching
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

@app.get("/items/{item_id}")
async def read_item_cached(item_id: int, db: Session = Depends(get_db)):
    """Get item with Redis caching."""
    cache_key = f"item:{item_id}"

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query database
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Cache result
    redis_client.setex(cache_key, 300, json.dumps(item.dict()))
    return item
```

### Background Tasks
```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    """Send email (slow operation)."""
    # Email sending logic
    pass

@app.post("/send-notification")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    """Send notification in background."""
    background_tasks.add_task(send_email, email, "Your notification")
    return {"message": "Notification will be sent"}
```

## Security

### Input Validation
```python
from pydantic import validator, Field
import re

class UserCreate(BaseModel):
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)

    @validator('username')
    def username_alphanumeric(cls, v):
        """Ensure username is alphanumeric."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v

    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain number')
        return v
```

### SQL Injection Prevention
```python
# ✅ Good: Use ORM with parameterized queries
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# ❌ Bad: Raw SQL without parameters
def get_user_unsafe(db: Session, user_id: str):
    return db.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginCredentials):
    """Login with rate limiting."""
    pass
```

## API Design

### Versioning
```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import items, users

api_router = APIRouter()
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# app/main.py
app.include_router(api_router, prefix="/api/v1")
```

### Consistent Response Format
```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: T
    message: str | None = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response."""
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

@app.get("/items", response_model=ApiResponse[list[Item]])
def read_items():
    items = get_items()
    return ApiResponse(data=items, message="Items retrieved successfully")
```

### RESTful Conventions
```python
# Resources should be plural nouns
@app.get("/items")          # List items
@app.post("/items")         # Create item
@app.get("/items/{id}")     # Get specific item
@app.put("/items/{id}")     # Update item (full)
@app.patch("/items/{id}")   # Update item (partial)
@app.delete("/items/{id}")  # Delete item

# Nested resources
@app.get("/users/{user_id}/items")  # Get user's items
```

## Documentation

### Comprehensive Docstrings
```python
@app.post("/items", response_model=Item, status_code=201)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new item.

    Args:
        item: Item data to create
        db: Database session
        current_user: Authenticated user

    Returns:
        Created item with generated ID

    Raises:
        HTTPException: If item name already exists
    """
    return crud.item.create(db, item, owner_id=current_user.id)
```

### OpenAPI Metadata
```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    description="Comprehensive API for managing resources",
    version="1.0.0",
    terms_of_service="https://example.com/terms",
    contact={
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)
```

### Response Examples
```python
@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Example Item",
                        "price": 29.99
                    }
                }
            }
        },
        404: {"description": "Item not found"}
    }
)
def read_item(item_id: int):
    """Get item by ID."""
    pass
```

## Configuration Best Practices

### Environment-Based Configuration
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    app_name: str = "FastAPI App"
    debug: bool = False
    database_url: str
    secret_key: str
    redis_url: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    """Get cached settings."""
    return Settings()

# Usage
settings = get_settings()
```

### Logging
```python
import logging
from fastapi import Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

## Checklist

### Development
- ✓ Follow consistent project structure
- ✓ Separate concerns (routes, models, schemas, CRUD)
- ✓ Use type hints everywhere
- ✓ Implement proper error handling
- ✓ Add comprehensive docstrings
- ✓ Use environment variables for configuration

### Performance
- ✓ Use async for I/O operations
- ✓ Implement caching where appropriate
- ✓ Optimize database queries
- ✓ Use background tasks for slow operations
- ✓ Enable GZIP compression

### Security
- ✓ Validate all inputs
- ✓ Use parameterized queries
- ✓ Implement rate limiting
- ✓ Use HTTPS in production
- ✓ Hash passwords with bcrypt
- ✓ Set appropriate CORS policies

### Testing
- ✓ Write tests for all endpoints
- ✓ Achieve >80% code coverage
- ✓ Test error cases
- ✓ Use fixtures for common setup

### Documentation
- ✓ Add endpoint descriptions
- ✓ Document request/response models
- ✓ Provide example responses
- ✓ Keep README up to date
