# Tech Stack Reference

## Frontend Stack

### Next.js 16+ (App Router)
- Use App Router (`/app` directory)
- Server Components by default
- Server Actions for form handling
- Client Components only when necessary (`"use client"`)

```typescript
// app/layout.tsx structure
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

### Tailwind CSS
- Mobile-first responsive design
- Use `cn()` utility for conditional classes
- Prefer component composition over utility sprawl

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### Component Architecture
```
/components
  /ui          # Reusable primitives (Button, Input, Card)
  /forms       # Form components (TaskForm, LoginForm)
  /layout      # Layout components (Header, Sidebar)
  /features    # Feature-specific (TaskList, TaskItem)
```

## Backend Stack

### FastAPI
- Async handlers by default
- Pydantic models for validation
- Dependency injection for auth

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session

app = FastAPI()

@app.get("/api/{user_id}/tasks")
async def get_tasks(user_id: str, session: Session = Depends(get_session)):
    tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
    return tasks
```

### SQLModel ORM
- Combines Pydantic + SQLAlchemy
- Type-safe database operations

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    title: str
    description: Optional[str] = None
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

## Database

### Neon Serverless PostgreSQL
- Connection pooling via `?sslmode=require`
- Use connection string from environment

```python
# database.py
from sqlmodel import create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

## Authentication

### Better Auth
- JWT-based authentication
- Consistent field naming between signup/login

#### Signup Fields (REQUIRED)
- username
- email
- password

#### Login Fields (REQUIRED)
- identifier (username OR email)
- password

```typescript
// Frontend auth service
export async function signup(data: {
  username: string;
  email: string;
  password: string;
}) {
  return fetch("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function login(data: {
  identifier: string;
  password: string;
}) {
  return fetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
```
