# Docker Fundamentals

## Table of Contents
- [Core Concepts](#core-concepts)
- [Dockerfile Best Practices](#dockerfile-best-practices)
- [Multi-Stage Builds](#multi-stage-builds)
- [Image Optimization](#image-optimization)
- [Networking](#networking)
- [Volumes and Data](#volumes-and-data)

## Core Concepts

### Images vs Containers
- **Image**: Read-only template with instructions for creating a container
- **Container**: Runnable instance of an image
- **Layer**: Each instruction in a Dockerfile creates a layer

### Image Layers
```
Layer 5: CMD ["node", "server.js"]     (metadata only)
Layer 4: COPY . .                       (app code)
Layer 3: RUN npm install                (dependencies)
Layer 2: WORKDIR /app                   (metadata only)
Layer 1: FROM node:20-alpine            (base image)
```

## Dockerfile Best Practices

### Instruction Order (Cache Optimization)
```dockerfile
# 1. Base image (rarely changes)
FROM python:3.12-slim

# 2. System dependencies (occasionally changes)
RUN apt-get update && apt-get install -y curl

# 3. Application dependencies (changes moderately)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 4. Application code (changes frequently)
COPY . .

# 5. Runtime configuration
CMD ["uvicorn", "main:app"]
```

### Non-Root User
```dockerfile
# Create user/group
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --create-home appuser

# Switch before copying app code
USER appuser
COPY --chown=appuser:appgroup . .
```

### Healthchecks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Environment Variables
```dockerfile
# Build-time variables
ARG NODE_VERSION=20

# Runtime variables with defaults
ENV NODE_ENV=production \
    PORT=3000
```

## Multi-Stage Builds

### Benefits
- Smaller final images (no build tools)
- Separate build and runtime dependencies
- Better security (fewer attack surfaces)

### Python Example
```dockerfile
# Build stage
FROM python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.12-slim
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*
```

### Node.js Example
```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
COPY --from=builder /app/dist ./dist
```

## Image Optimization

### Base Image Selection
| Base Image | Size | Use Case |
|------------|------|----------|
| `alpine` | ~5MB | Minimal, musl libc |
| `slim` | ~80MB | Debian minimal |
| `bookworm` | ~120MB | Full Debian |
| `scratch` | 0MB | Static binaries only |

### Minimize Layers
```dockerfile
# Bad: Multiple RUN commands
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean

# Good: Single RUN command
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### .dockerignore
```
node_modules
.git
.env
*.md
__pycache__
.pytest_cache
```

## Networking

### Bridge Network (Default)
```bash
# Create network
docker network create app-network

# Run container on network
docker run --network app-network --name api myapp
```

### Container DNS
Containers on the same network can reach each other by name:
```
http://api:8000    # From frontend to backend
http://db:5432     # From backend to database
```

### Port Mapping
```bash
# HOST_PORT:CONTAINER_PORT
docker run -p 8080:8000 myapp    # Host 8080 → Container 8000
docker run -p 8000 myapp         # Random host port → Container 8000
```

## Volumes and Data

### Named Volumes
```yaml
# docker-compose.yml
volumes:
  postgres-data:

services:
  db:
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

### Bind Mounts (Development)
```yaml
services:
  app:
    volumes:
      - ./src:/app/src:ro    # Read-only source mount
```

### Volume Commands
```bash
docker volume ls                    # List volumes
docker volume create mydata         # Create volume
docker volume inspect mydata        # Inspect volume
docker volume rm mydata             # Remove volume
docker volume prune                 # Remove unused volumes
```

## Essential Commands

### Build
```bash
docker build -t myapp:v1 .
docker build -t myapp:v1 -f Dockerfile.prod .
docker build --no-cache -t myapp:v1 .
```

### Run
```bash
docker run -d --name myapp -p 8000:8000 myapp:v1
docker run -it --rm myapp:v1 /bin/sh
docker run --env-file .env myapp:v1
```

### Inspect
```bash
docker ps                           # Running containers
docker ps -a                        # All containers
docker logs myapp                   # Container logs
docker logs -f myapp                # Follow logs
docker exec -it myapp /bin/sh       # Shell into container
```

### Clean Up
```bash
docker system prune                 # Remove unused data
docker image prune -a               # Remove unused images
docker container prune              # Remove stopped containers
```
