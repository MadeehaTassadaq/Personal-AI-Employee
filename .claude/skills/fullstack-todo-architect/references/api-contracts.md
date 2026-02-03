# API Contracts Reference

## Task API Endpoints

### GET /api/{user_id}/tasks
List all tasks for a user.

**Response 200:**
```json
[
  {
    "id": 1,
    "user_id": "user123",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### POST /api/{user_id}/tasks
Create a new task.

**Request:**
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread"
}
```

**Response 201:**
```json
{
  "id": 1,
  "user_id": "user123",
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/{user_id}/tasks/{id}
Get a specific task.

**Response 200:**
```json
{
  "id": 1,
  "user_id": "user123",
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Response 404:**
```json
{
  "detail": "Task not found"
}
```

### PUT /api/{user_id}/tasks/{id}
Update a task.

**Request:**
```json
{
  "title": "Buy groceries today",
  "description": "Milk, eggs, bread, butter"
}
```

**Response 200:**
```json
{
  "id": 1,
  "user_id": "user123",
  "title": "Buy groceries today",
  "description": "Milk, eggs, bread, butter",
  "completed": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### DELETE /api/{user_id}/tasks/{id}
Delete a task.

**Response 204:** No content

**Response 404:**
```json
{
  "detail": "Task not found"
}
```

### PATCH /api/{user_id}/tasks/{id}/complete
Toggle task completion status.

**Response 200:**
```json
{
  "id": 1,
  "user_id": "user123",
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

## Auth API Endpoints

### POST /api/auth/signup
Register a new user.

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response 201:**
```json
{
  "id": "user123",
  "username": "johndoe",
  "email": "john@example.com",
  "token": "jwt.token.here"
}
```

**Response 400:**
```json
{
  "detail": "Username already exists"
}
```

### POST /api/auth/login
Authenticate a user.

**Request:**
```json
{
  "identifier": "johndoe",
  "password": "securepassword123"
}
```

**Response 200:**
```json
{
  "id": "user123",
  "username": "johndoe",
  "email": "john@example.com",
  "token": "jwt.token.here"
}
```

**Response 401:**
```json
{
  "detail": "Invalid credentials"
}
```

## Error Response Format

All errors follow this format:
```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| NOT_FOUND | 404 | Resource not found |
| UNAUTHORIZED | 401 | Invalid or missing auth |
| FORBIDDEN | 403 | Not allowed to access resource |
| VALIDATION_ERROR | 422 | Invalid request data |
| CONFLICT | 409 | Resource already exists |
