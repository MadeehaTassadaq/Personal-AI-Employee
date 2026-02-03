---
name: fullstack-ai-engineer
description: Senior-level full-stack AI engineering skill for building production-ready web applications with Next.js 16+ frontend, FastAPI backend, JWT authentication, PostgreSQL/SQLModel database, AI chatbot integration, Hugging Face Spaces deployment, and Docker containerization. Use when (1) building full-stack web apps with Next.js + FastAPI, (2) implementing JWT authentication flows, (3) setting up PostgreSQL with SQLModel, (4) adding AI chatbot backends, (5) deploying to Hugging Face Spaces, (6) containerizing with Docker, (7) creating production-ready APIs with proper auth middleware.
---

# Full-Stack AI Engineer

Senior-level expertise for building production-ready web applications combining Next.js, FastAPI, PostgreSQL, AI integration, and cloud deployment.

## Architecture Decision Tree

```
User Request
    │
    ├─► "Build full-stack app" ──► Start with Project Setup
    ├─► "Add authentication" ──► JWT Auth Workflow
    ├─► "Add database" ──► PostgreSQL + SQLModel
    ├─► "Add AI chatbot" ──► Chatbot Integration
    ├─► "Deploy to cloud" ──► Hugging Face Deployment
    └─► "Containerize" ──► Docker Workflow
```

## Tech Stack Reference

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 16+ (App Router) | React SSR/SSG framework |
| Backend | FastAPI | Async Python API |
| Auth | JWT + bcrypt | Stateless authentication |
| Database | PostgreSQL + SQLModel | ORM with Pydantic validation |
| AI | OpenAI/Agents SDK | Chatbot integration |
| Deploy | Hugging Face Spaces | Cloud hosting |
| Container | Docker | Reproducible environments |

## Core Workflows

### 1. Project Setup

**Directory Structure:**
```
project/
├── frontend/           # Next.js 16+ App Router
│   ├── src/
│   │   ├── app/       # App Router pages
│   │   ├── components/
│   │   ├── lib/       # API client, utilities
│   │   ├── services/  # API service layer
│   │   ├── context/   # React contexts (auth)
│   │   └── types/     # TypeScript definitions
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── models/    # SQLModel schemas
│   │   ├── middleware/# Auth middleware
│   │   ├── main.py    # FastAPI app
│   │   └── database.py
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml
```

**Backend Entry Point Pattern:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. JWT Authentication

See [references/jwt-auth.md](references/jwt-auth.md) for complete patterns.

**Quick Reference - Token Flow:**
```
1. POST /api/auth/register → Create user (hash password)
2. POST /api/auth/token → Validate credentials → Return JWT
3. Protected routes → Extract token → Verify → Get current_user
```

**Key Patterns:**
- Password hashing: `bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())`
- Token creation: `jwt.encode({"sub": email, "user_id": str(id), "exp": expiry}, SECRET_KEY, algorithm="HS256")`
- Middleware: OAuth2PasswordBearer + Depends(get_current_user)

### 3. PostgreSQL + SQLModel

See [references/database.md](references/database.md) for schema patterns.

**Model Pattern:**
```python
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4
from datetime import datetime

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Database Connection:**
```python
from sqlmodel import create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

### 4. Next.js Frontend

See [references/nextjs.md](references/nextjs.md) for component patterns.

**Auth Context Pattern:**
```typescript
// context/AuthContext.tsx
export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });
    const data = await res.json();
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
  };
};
```

**Authenticated Fetch:**
```typescript
// lib/api-client.ts
export const authFetch = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('token');
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    },
  });
};
```

### 5. AI Chatbot Integration

See [references/chatbot.md](references/chatbot.md) for AI patterns.

**OpenAI Integration Pattern:**
```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def chat_completion(messages: list[dict], system_prompt: str = None):
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.extend(messages)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=msgs,
        temperature=0.7,
    )
    return response.choices[0].message.content
```

### 6. Docker Containerization

See [assets/docker/](assets/docker/) for templates.

**Production Dockerfile:**
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### 7. Hugging Face Deployment

See [references/huggingface.md](references/huggingface.md) for deployment guide.

**Key Requirements:**
1. Port 7860 (HF default)
2. `PORT` env var support: `--port ${PORT:-7860}`
3. CORS for HF domain
4. Secrets via HF Secrets UI

**HF Space Setup:**
```bash
# Create Space via HF CLI or UI
huggingface-cli login
huggingface-cli repo create <space-name> --type space --space-sdk docker

# Push Docker image
git remote add hf https://huggingface.co/spaces/<user>/<space>
git push hf main
```

## Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@host:5432/db
BETTER_AUTH_SECRET=your-jwt-secret-key
OPENAI_API_KEY=sk-...

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Error Handling Patterns

**FastAPI Error Handler:**
```python
@router.post("/endpoint")
def endpoint(data: Schema, session: Session = Depends(get_session)):
    try:
        # Business logic
        return result
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

**Frontend Error Boundary:**
```typescript
// Handle 401 globally
if (response.status === 401) {
  localStorage.removeItem('token');
  window.location.href = '/login';
}
```

## Testing Checklist

- [ ] Auth: Register → Login → Access protected route
- [ ] CRUD: Create, Read, Update, Delete operations
- [ ] Validation: Invalid inputs return proper errors
- [ ] Docker: Build and run locally
- [ ] Deploy: Health check endpoint responds

## References

- **[jwt-auth.md](references/jwt-auth.md)**: Complete JWT authentication patterns
- **[database.md](references/database.md)**: SQLModel schemas and migrations
- **[nextjs.md](references/nextjs.md)**: Next.js 16+ component patterns
- **[chatbot.md](references/chatbot.md)**: AI chatbot integration
- **[huggingface.md](references/huggingface.md)**: Deployment to HF Spaces

## Assets

- **[assets/docker/](assets/docker/)**: Dockerfile and docker-compose templates
