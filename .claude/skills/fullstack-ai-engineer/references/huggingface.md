# Hugging Face Spaces Deployment Reference

## Table of Contents
- [Space Setup](#space-setup)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [CORS Configuration](#cors-configuration)
- [Secrets Management](#secrets-management)
- [Troubleshooting](#troubleshooting)

## Space Setup

### Create a Docker Space

1. **Via Hugging Face UI:**
   - Go to huggingface.co/spaces
   - Click "Create new Space"
   - Choose Docker as SDK
   - Set visibility (public/private)

2. **Via CLI:**
```bash
# Install CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Create space
huggingface-cli repo create <space-name> --type space --space-sdk docker
```

### Space Configuration

Create `README.md` in your space root:
```yaml
---
title: My FastAPI App
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---
```

## Docker Deployment

### Dockerfile for Hugging Face

```dockerfile
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Expose port (HF uses 7860 by default)
EXPOSE 7860

# Use PORT env var (HF may override)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
```

### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlmodel==0.0.16
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
bcrypt==4.1.2
openai>=1.0.0
```

### Push to Hugging Face

```bash
# Clone your space
git clone https://huggingface.co/spaces/<username>/<space-name>
cd <space-name>

# Copy your backend files
cp -r ../project/backend/* .

# Commit and push
git add .
git commit -m "Deploy FastAPI backend"
git push
```

## Environment Configuration

### Port Configuration

Hugging Face sets `PORT` environment variable. Your app must respect it:

```python
# main.py
import os
PORT = int(os.getenv("PORT", 7860))
```

Or in Dockerfile:
```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
```

### Health Check

Add health endpoint for HF monitoring:

```python
@app.get("/")
def root():
    return {"status": "running", "message": "API is healthy"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

## CORS Configuration

Configure CORS for Hugging Face Spaces and your frontend:

```python
from fastapi.middleware.cors import CORSMiddleware

# Define allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://huggingface.co",
    "https://*.hf.space",  # Hugging Face Spaces
    "https://your-frontend.vercel.app",  # Your frontend domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Dynamic CORS (Development)

```python
import os

def get_allowed_origins():
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Add HF Space origin
    space_host = os.getenv("SPACE_HOST")
    if space_host:
        origins.append(f"https://{space_host}")

    # Add custom frontend
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)

    return origins
```

## Secrets Management

### Setting Secrets in HF Spaces

1. Go to Space Settings
2. Navigate to "Repository secrets"
3. Add secrets:
   - `DATABASE_URL`
   - `BETTER_AUTH_SECRET`
   - `OPENAI_API_KEY`

### Accessing Secrets in Code

Secrets are available as environment variables:

```python
import os
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

# These work both locally (.env) and on HF (secrets)
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### Required Secrets

| Secret Name | Description |
|-------------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `BETTER_AUTH_SECRET` | JWT signing secret |
| `OPENAI_API_KEY` | OpenAI API key (for chatbot) |

## Troubleshooting

### Common Issues

**1. Build Fails**
```bash
# Check build logs in HF Space
# Ensure Dockerfile has correct base image
# Verify requirements.txt has all dependencies
```

**2. App Not Starting**
```python
# Verify PORT binding
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

# Check health endpoint returns 200
GET / or GET /health
```

**3. Database Connection Fails**
```python
# Ensure DATABASE_URL secret is set
# Check PostgreSQL accepts connections from HF IPs
# Use connection pooling for serverless
```

**4. CORS Errors**
```python
# Add HF Space domain to CORS origins
# Check credentials setting
# Verify headers are allowed
```

### Logs

View logs in HF Space:
1. Go to Space page
2. Click "Logs" tab
3. Check runtime errors

### Local Testing Before Deploy

```bash
# Build Docker image
docker build -t myapp .

# Run with same port
docker run -p 7860:7860 \
  -e DATABASE_URL=your_db_url \
  -e BETTER_AUTH_SECRET=your_secret \
  myapp

# Test endpoints
curl http://localhost:7860/health
```

## Frontend Integration

### Connecting Frontend to HF Space

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL ||
  'https://<username>-<space-name>.hf.space';

export const api = {
  baseUrl: API_URL,

  async fetch(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem('token');

    return fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
    });
  }
};
```

### Environment Variables

```bash
# Frontend .env.local (production)
NEXT_PUBLIC_API_URL=https://<username>-<space-name>.hf.space

# Frontend .env.local (development)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment Checklist

- [ ] Dockerfile builds successfully locally
- [ ] Health endpoint returns 200
- [ ] CORS configured for frontend domain
- [ ] All secrets set in HF Space settings
- [ ] Database accepts connections from HF
- [ ] Frontend API URL points to HF Space
- [ ] SSL/HTTPS working (automatic on HF)
