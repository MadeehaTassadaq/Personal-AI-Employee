# FastAPI Core Concepts

## Table of Contents
- [Path Operations](#path-operations)
- [Request and Response Models](#request-and-response-models)
- [Dependency Injection](#dependency-injection)
- [Path and Query Parameters](#path-and-query-parameters)
- [Request Body](#request-body)
- [Response Models](#response-models)
- [Status Codes](#status-codes)

## Path Operations

FastAPI uses Python type hints to define API endpoints (path operations):

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items")
async def create_item(item: Item):
    return item

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"deleted": item_id}
```

### HTTP Methods
- `@app.get()` - Read/retrieve data
- `@app.post()` - Create new data
- `@app.put()` - Update existing data (full update)
- `@app.patch()` - Partial update
- `@app.delete()` - Delete data
- `@app.options()`, `@app.head()` - HTTP metadata

## Request and Response Models

Use Pydantic models for automatic validation and serialization:

```python
from pydantic import BaseModel, Field
from typing import Optional

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    tax: Optional[float] = None
    tags: list[str] = []

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

@app.post("/items", response_model=ItemResponse)
async def create_item(item: Item):
    # Automatically validates and serializes
    return {"id": 1, **item.dict()}
```

### Key Pydantic Features
- Automatic validation
- Type coercion
- Field constraints (min/max, regex, etc.)
- Default values
- Optional fields with `Optional` or `| None`

## Dependency Injection

Dependencies provide reusable logic:

```python
from fastapi import Depends, Header, HTTPException

# Simple dependency
def get_query_param(q: str | None = None):
    return q

# Dependency with validation
async def get_token_header(x_token: str = Header()):
    if x_token != "secret-token":
        raise HTTPException(status_code=400, detail="Invalid token")
    return x_token

# Nested dependencies
async def get_current_user(token: str = Depends(get_token_header)):
    # Validate token and return user
    return {"username": "user"}

@app.get("/items")
async def read_items(
    q: str = Depends(get_query_param),
    user: dict = Depends(get_current_user)
):
    return {"q": q, "user": user}
```

### Dependency Patterns
- **Class dependencies**: Use classes for stateful dependencies
- **Yield dependencies**: For setup/teardown (e.g., database sessions)
- **Dependency chains**: Dependencies can depend on other dependencies
- **Global dependencies**: Apply to all routes with `app = FastAPI(dependencies=[...])`

## Path and Query Parameters

### Path Parameters
```python
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: str):
    return {"user_id": user_id, "item_id": item_id}
```

### Query Parameters
```python
from fastapi import Query

@app.get("/items")
async def read_items(
    skip: int = 0,
    limit: int = Query(10, le=100),  # Max 100
    q: str | None = Query(None, min_length=3)
):
    return {"skip": skip, "limit": limit, "q": q}
```

### Parameter Validation
```python
from pydantic import Field

@app.get("/items")
async def read_items(
    skip: int = Query(0, ge=0),  # Greater than or equal to 0
    limit: int = Query(10, le=100),  # Less than or equal to 100
    q: str = Query(..., min_length=3, max_length=50)  # Required
):
    return {"skip": skip, "limit": limit, "q": q}
```

## Request Body

Multiple body parameters:

```python
from fastapi import Body

@app.put("/items/{item_id}")
async def update_item(
    item_id: int,
    item: Item,
    user: User,
    importance: int = Body(...)  # Single value as body
):
    return {"item_id": item_id, "item": item, "user": user, "importance": importance}
```

Nested models:

```python
class Image(BaseModel):
    url: str
    name: str

class Item(BaseModel):
    name: str
    images: list[Image]  # Nested list

@app.post("/items")
async def create_item(item: Item):
    return item
```

## Response Models

### Exclude Fields
```python
class UserIn(BaseModel):
    username: str
    password: str
    email: str

class UserOut(BaseModel):
    username: str
    email: str

@app.post("/users", response_model=UserOut)
async def create_user(user: UserIn):
    return user  # Password automatically excluded
```

### Multiple Response Models
```python
from fastapi import status

@app.get("/items/{item_id}",
         response_model=Item,
         responses={
             404: {"model": Message, "description": "Item not found"}
         })
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

## Status Codes

Use appropriate HTTP status codes:

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    return None

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return items[item_id]
```

Common status codes:
- **200 OK**: Success (GET, PUT)
- **201 Created**: Resource created (POST)
- **204 No Content**: Success with no response body (DELETE)
- **400 Bad Request**: Invalid input
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Validation error (automatic)
- **500 Internal Server Error**: Server error
