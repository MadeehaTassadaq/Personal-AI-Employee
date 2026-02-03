---
name: secure-fullstack-orchestrator
description: Act as a Full-Stack Integration Architect. Master the connection between Next.js Frontend and FastAPI Backend using the Hackathon Stack. Expert in database expertise (SQLModel + Neon), auth bridge (Better Auth + FastAPI), frontend integration, monorepo coordination, and execution protocol. Use when connecting frontend and backend components, implementing authentication middleware, or orchestrating full-stack features.
---

# Skill: Secure-FullStack-Orchestrator

## Overview

Act as a Full-Stack Integration Architect. Master the connection between a Next.js Frontend and a FastAPI Backend using the specific Hackathon Stack.

## 1. THE DATABASE EXPERTISE (SQLModel + Neon)

### Schema Design
- **Every table MUST have a `user_id` column (string) to ensure multi-tenant isolation.**
- Example:
```python
class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True)  # Critical for multi-tenant isolation
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Neon Optimization
- Use `DATABASE_URL` with pooled connections
- Example configuration:
```python
from sqlmodel import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=0)
```

### Migration Strategy
- Use SQLModel's `create_db_and_tables` on startup for early phases
- Structure code for easy migration to Alembic later
- Example startup function:
```python
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

## 2. THE AUTH BRIDGE (Better Auth + FastAPI Integration)

### Issuer Configuration
- Next.js (Frontend) handles OAuth (Google/GitHub) via `Better Auth`
- Better Auth is configured to issue JWTs
- The Backend (FastAPI) MUST share the `BETTER_AUTH_SECRET`

### The JWT Handshake
- Configure Better Auth with JWT settings:
```javascript
// frontend/.better-auth.config.js
export default {
  jwt: {
    secret: process.env.BETTER_AUTH_SECRET,
    expiresIn: "7d"
  }
}
```

### Backend Middleware
Implement a custom `AuthMiddleware` in FastAPI that:
1. Extracts the Bearer token from the Authorization header
2. Decodes and verifies the JWT using the shared secret
3. Injects the `current_user` object into the request state

Example implementation:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel import Session
from typing import Optional
import os

security = HTTPBearer()

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, os.getenv("BETTER_AUTH_SECRET"), algorithms=["HS256"])
        return payload
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

# Usage in route:
@app.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user.get("user_id")}
```

### Security Rule
- If a request reaches a PROTECTED route without a valid JWT, return `401 Unauthorized`

## 3. SEAMLESS FRONTEND INTEGRATION

### CORS Policy
- Configure FastAPI to allow requests from the Next.js URL (and localhost during dev):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],  # Next.js URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### The API Client
Build a unified TypeScript client in `frontend/lib/api.ts` that:
- Automatically retrieves the session/token from Better Auth
- Attaches it as `Authorization: Bearer <token>` to every request
- Handles 401 errors by redirecting users to the login page

Example implementation:
```typescript
// frontend/lib/api.ts
import { getAuthSession } from "better-auth/client";

class ApiClient {
  private baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async request(endpoint: string, options: RequestInit = {}) {
    const session = await getAuthSession();

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (session?.token) {
      headers['Authorization'] = `Bearer ${session.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Redirect to login page
      window.location.href = '/login';
      return;
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient();
```

## 4. MONOREPO COORDINATION

### Feature Implementation
- When implementing features, check both `phases/phase-X/frontend` and `phases/phase-X/backend`
- Ensure Pydantic models in the Backend match the TypeScript Interfaces in the Frontend 1:1

Example:
```python
# backend/models/user.py
from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    name: str
```

```typescript
// frontend/types/user.ts
export interface User {
  id: string;
  email: string;
  name: string;
}
```

## 5. EXECUTION PROTOCOL

When this skill is invoked:

1. **Initialize the Auth configuration on the Frontend first**
   - Set up Better Auth with proper JWT configuration
   - Configure the auth provider in Next.js

2. **Implement the JWT validation logic on the Backend second**
   - Create the authentication middleware
   - Set up the shared secret
   - Implement protected routes

3. **Test the "Secure Bridge" by performing a simple "Me/Profile" API call before building the Todo logic**
   - Create a `/me` endpoint that returns current user info
   - Verify the JWT token is properly validated
   - Confirm user isolation is working

## Implementation Checklist

- [ ] Database tables have `user_id` column for multi-tenant isolation
- [ ] Better Auth configured with JWT settings on frontend
- [ ] Shared `BETTER_AUTH_SECRET` between frontend and backend
- [ ] FastAPI middleware validates JWT tokens
- [ ] CORS configured for frontend domain
- [ ] API client automatically attaches auth headers
- [ ] 401 responses redirect to login page
- [ ] Pydantic models match TypeScript interfaces
- [ ] `/me` endpoint works for testing auth flow