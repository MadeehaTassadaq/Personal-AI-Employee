# FastAPI Testing Guide

## Table of Contents
- [Test Setup](#test-setup)
- [Basic Testing](#basic-testing)
- [Testing with Database](#testing-with-database)
- [Testing Authentication](#testing-authentication)
- [Async Testing](#async-testing)
- [Test Fixtures](#test-fixtures)
- [Mocking](#mocking)

## Test Setup

### Installation
```bash
pip install pytest httpx pytest-asyncio
```

### Project Structure
```
project/
├── app/
│   ├── main.py
│   ├── models.py
│   └── routes.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_main.py
    └── test_routes.py
```

### pytest.ini Configuration
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
asyncio_mode = auto
```

## Basic Testing

### TestClient Setup
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item():
    """Test POST endpoint."""
    response = client.post(
        "/items",
        json={"name": "Test Item", "price": 10.99}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data

def test_validation_error():
    """Test validation error handling."""
    response = client.post(
        "/items",
        json={"name": "Test"}  # Missing required field
    )
    assert response.status_code == 422  # Unprocessable Entity
```

### Testing Query Parameters
```python
def test_query_parameters():
    """Test query parameter handling."""
    response = client.get("/items?skip=0&limit=10")
    assert response.status_code == 200

    response = client.get("/items?skip=-1")  # Invalid
    assert response.status_code == 422

def test_path_parameters():
    """Test path parameter validation."""
    response = client.get("/items/1")
    assert response.status_code == 200

    response = client.get("/items/invalid")
    assert response.status_code == 422
```

### Testing Headers
```python
def test_custom_headers():
    """Test custom header handling."""
    response = client.get(
        "/secure",
        headers={"X-Token": "secret-token"}
    )
    assert response.status_code == 200

def test_missing_header():
    """Test missing required header."""
    response = client.get("/secure")
    assert response.status_code == 422
```

## Testing with Database

### Database Test Fixture
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def db_session():
    """Create test database session."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### Testing CRUD Operations
```python
def test_create_and_read_item(client):
    """Test creating and reading an item."""
    # Create
    response = client.post(
        "/items",
        json={"name": "Test Item", "price": 10.99}
    )
    assert response.status_code == 201
    item_id = response.json()["id"]

    # Read
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"

def test_update_item(client, db_session):
    """Test updating an item."""
    # Create item first
    from app.models import Item
    db_item = Item(name="Original", price=10.0)
    db_session.add(db_item)
    db_session.commit()

    # Update
    response = client.put(
        f"/items/{db_item.id}",
        json={"name": "Updated", "price": 15.0}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"

def test_delete_item(client, db_session):
    """Test deleting an item."""
    from app.models import Item
    db_item = Item(name="To Delete", price=10.0)
    db_session.add(db_item)
    db_session.commit()

    response = client.delete(f"/items/{db_item.id}")
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/items/{db_item.id}")
    assert response.status_code == 404
```

## Testing Authentication

### Auth Test Fixtures
```python
@pytest.fixture
def test_user(db_session):
    """Create test user."""
    from app.models import User
    from app.core.auth import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123")
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token."""
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass123"}
    )
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}
```

### Testing Protected Endpoints
```python
def test_access_without_auth(client):
    """Test accessing protected endpoint without auth."""
    response = client.get("/users/me")
    assert response.status_code == 401

def test_access_with_auth(client, auth_headers):
    """Test accessing protected endpoint with auth."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_invalid_token(client):
    """Test with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401

def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401
```

## Async Testing

### Async Test Setup
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    """Test async endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
```

### Testing Async Database Operations
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def async_db_session():
    """Create async test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///./test.db")
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_async_crud(async_db_session):
    """Test async CRUD operations."""
    from app.crud import create_item_async

    item = await create_item_async(
        async_db_session,
        {"name": "Test", "price": 10.0}
    )
    assert item.name == "Test"
```

## Test Fixtures

### Common Fixtures
```python
# tests/conftest.py

@pytest.fixture(scope="session")
def app():
    """Create application instance."""
    from app.main import app
    return app

@pytest.fixture
def sample_items():
    """Sample item data."""
    return [
        {"name": "Item 1", "price": 10.0},
        {"name": "Item 2", "price": 20.0},
        {"name": "Item 3", "price": 30.0},
    ]

@pytest.fixture
def populate_db(db_session, sample_items):
    """Populate database with sample data."""
    from app.models import Item
    for item_data in sample_items:
        db_session.add(Item(**item_data))
    db_session.commit()

def test_list_items(client, populate_db):
    """Test listing items."""
    response = client.get("/items")
    assert response.status_code == 200
    assert len(response.json()) == 3
```

## Mocking

### Mocking External APIs
```python
from unittest.mock import patch, MagicMock

@patch("app.services.external_api.get_data")
def test_with_mock_api(mock_get_data, client):
    """Test with mocked external API."""
    mock_get_data.return_value = {"status": "success"}

    response = client.get("/external-data")
    assert response.status_code == 200
    mock_get_data.assert_called_once()
```

### Mocking Dependencies
```python
from app.main import app
from app.dependencies import get_current_user

def test_override_dependency(client):
    """Test with overridden dependency."""
    def mock_current_user():
        return {"username": "mockuser", "id": 999}

    app.dependency_overrides[get_current_user] = mock_current_user

    response = client.get("/users/me")
    assert response.json()["username"] == "mockuser"

    app.dependency_overrides.clear()
```

### Mocking Database Queries
```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_mock_database_query():
    """Test with mocked database query."""
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        {"id": 1, "name": "Item 1"}
    ]

    result = await get_items(mock_db)
    assert len(result) == 1
    mock_db.execute.assert_called_once()
```

## Best Practices

### Test Organization
```python
class TestItemEndpoints:
    """Group related tests in classes."""

    def test_create_item(self, client):
        """Test item creation."""
        pass

    def test_read_item(self, client):
        """Test reading item."""
        pass

    def test_update_item(self, client):
        """Test updating item."""
        pass

    def test_delete_item(self, client):
        """Test deleting item."""
        pass
```

### Parametrized Tests
```python
@pytest.mark.parametrize("name,price,expected_status", [
    ("Valid Item", 10.0, 201),
    ("", 10.0, 422),  # Empty name
    ("Item", -5.0, 422),  # Negative price
    ("Item", 0, 422),  # Zero price
])
def test_create_item_validation(client, name, price, expected_status):
    """Test item creation validation."""
    response = client.post(
        "/items",
        json={"name": name, "price": price}
    )
    assert response.status_code == expected_status
```

### Coverage
```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### Testing Checklist
- ✓ Test all endpoints (GET, POST, PUT, DELETE)
- ✓ Test validation errors
- ✓ Test authentication and authorization
- ✓ Test database operations
- ✓ Test edge cases and error handling
- ✓ Use fixtures for common setup
- ✓ Mock external dependencies
- ✓ Maintain >80% code coverage
- ✓ Use descriptive test names
- ✓ Keep tests independent and isolated
