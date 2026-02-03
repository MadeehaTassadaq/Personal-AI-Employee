#!/usr/bin/env python3
"""
Initialize a new FastAPI project with recommended structure and configuration.

Usage: python init_project.py <project_name> [--database sqlalchemy|none] [--auth]
"""

import argparse
import os
from pathlib import Path


def create_project_structure(project_name: str, use_db: str = "none", use_auth: bool = False):
    """Create FastAPI project directory structure."""
    base_path = Path(project_name)

    # Main directories
    dirs = [
        base_path / "app",
        base_path / "app" / "api",
        base_path / "app" / "api" / "v1",
        base_path / "app" / "core",
        base_path / "app" / "models",
        base_path / "app" / "schemas",
        base_path / "app" / "crud",
        base_path / "tests",
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / "__init__.py").touch()

    # Create main files
    create_main_file(base_path)
    create_config_file(base_path, use_db)
    create_requirements_file(base_path, use_db, use_auth)
    create_env_file(base_path)
    create_dockerfile(base_path)
    create_docker_compose(base_path, use_db)
    create_gitignore(base_path)
    create_readme(base_path, project_name)

    if use_db != "none":
        create_database_files(base_path)

    if use_auth:
        create_auth_files(base_path)

    create_example_router(base_path)
    create_test_file(base_path)

    print(f"✅ FastAPI project '{project_name}' created successfully!")
    print(f"\nNext steps:")
    print(f"1. cd {project_name}")
    print(f"2. python -m venv venv")
    print(f"3. source venv/bin/activate  # or venv\\Scripts\\activate on Windows")
    print(f"4. pip install -r requirements.txt")
    print(f"5. uvicorn app.main:app --reload")


def create_main_file(base_path: Path):
    content = '''"""Main FastAPI application module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
'''
    (base_path / "app" / "main.py").write_text(content)


def create_config_file(base_path: Path, use_db: str):
    db_url = ""
    if use_db == "sqlalchemy":
        db_url = '''    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
'''

    content = f'''"""Application configuration."""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "FastAPI Application"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
{db_url}
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
'''
    (base_path / "app" / "core" / "config.py").write_text(content)


def create_requirements_file(base_path: Path, use_db: str, use_auth: bool):
    requirements = [
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-multipart>=0.0.9",
    ]

    if use_db == "sqlalchemy":
        requirements.extend([
            "sqlalchemy>=2.0.0",
            "alembic>=1.13.0",
            "psycopg2-binary>=2.9.9",  # PostgreSQL
        ])

    if use_auth:
        requirements.extend([
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.9",
        ])

    requirements.extend([
        "",
        "# Development dependencies",
        "pytest>=8.0.0",
        "httpx>=0.27.0",
        "pytest-asyncio>=0.23.0",
    ])

    (base_path / "requirements.txt").write_text("\n".join(requirements))


def create_env_file(base_path: Path):
    content = '''# Application settings
PROJECT_NAME="My FastAPI Project"
API_V1_STR="/api/v1"

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Database (if using)
# DATABASE_URL=postgresql://user:password@localhost/dbname

# Security (if using auth)
# SECRET_KEY=your-secret-key-here
# ALGORITHM=HS256
# ACCESS_TOKEN_EXPIRE_MINUTES=30
'''
    (base_path / ".env.example").write_text(content)
    (base_path / ".env").write_text(content)


def create_dockerfile(base_path: Path):
    content = '''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app ./app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    (base_path / "Dockerfile").write_text(content)


def create_docker_compose(base_path: Path, use_db: str):
    db_service = ""
    if use_db == "sqlalchemy":
        db_service = '''
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: dbname
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
'''

    content = f'''version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db/dbname
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --reload
{db_service}'''
    (base_path / "docker-compose.yml").write_text(content)


def create_gitignore(base_path: Path):
    content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# FastAPI
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Database
*.db
*.sqlite3

# Logs
*.log
'''
    (base_path / ".gitignore").write_text(content)


def create_readme(base_path: Path, project_name: str):
    content = f'''# {project_name}

FastAPI backend application.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Docker

Run with Docker Compose:
```bash
docker-compose up
```

## Testing

Run tests:
```bash
pytest
```

## Project Structure

```
{project_name}/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── __init__.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   ├── schemas/
│   ├── crud/
│   └── main.py
├── tests/
├── .env
├── requirements.txt
└── Dockerfile
```
'''
    (base_path / "README.md").write_text(content)


def create_database_files(base_path: Path):
    # Database session
    db_content = '''"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    (base_path / "app" / "core" / "database.py").write_text(db_content)

    # Example model
    model_content = '''"""Example database model."""
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class Item(Base):
    """Item model."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    is_active = Column(Boolean, default=True)
'''
    (base_path / "app" / "models" / "item.py").write_text(model_content)


def create_auth_files(base_path: Path):
    auth_content = '''"""Authentication utilities."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate token and return current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username}
'''
    (base_path / "app" / "core" / "auth.py").write_text(auth_content)


def create_example_router(base_path: Path):
    router_content = '''"""Example API router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Item(BaseModel):
    """Item schema."""
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


items_db = {}


@router.get("/items")
async def list_items():
    """List all items."""
    return {"items": list(items_db.values())}


@router.post("/items", status_code=201)
async def create_item(item: Item):
    """Create a new item."""
    item_id = len(items_db) + 1
    items_db[item_id] = {"id": item_id, **item.model_dump()}
    return items_db[item_id]


@router.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get item by ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@router.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    """Update an item."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id].update(item.model_dump())
    return items_db[item_id]


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    """Delete an item."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return None
'''
    (base_path / "app" / "api" / "v1" / "items.py").write_text(router_content)

    init_content = '''"""API v1 router."""
from fastapi import APIRouter
from app.api.v1 import items

router = APIRouter()
router.include_router(items.router, prefix="/items", tags=["items"])
'''
    (base_path / "app" / "api" / "v1" / "__init__.py").write_text(init_content)


def create_test_file(base_path: Path):
    test_content = '''"""Test example endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_item():
    """Test creating an item."""
    item_data = {
        "name": "Test Item",
        "description": "A test item",
        "price": 29.99,
        "tax": 2.50
    }
    response = client.post("/api/v1/items", json=item_data)
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"


def test_list_items():
    """Test listing items."""
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    assert "items" in response.json()
'''
    (base_path / "tests" / "test_api.py").write_text(test_content)


def main():
    parser = argparse.ArgumentParser(description="Initialize a FastAPI project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument(
        "--database",
        choices=["sqlalchemy", "none"],
        default="none",
        help="Database setup (default: none)"
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Include authentication setup"
    )

    args = parser.parse_args()
    create_project_structure(args.project_name, args.database, args.auth)


if __name__ == "__main__":
    main()
