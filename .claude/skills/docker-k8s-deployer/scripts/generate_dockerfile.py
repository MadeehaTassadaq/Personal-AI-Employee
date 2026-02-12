#!/usr/bin/env python3
"""
Dockerfile Generator - Creates optimized Dockerfiles for web applications

Usage:
    generate_dockerfile.py --type <fastapi|vite|nextjs> [options]

Options:
    --type          Application type: fastapi, vite, nextjs (required)
    --python-version  Python version for FastAPI (default: 3.12)
    --node-version    Node version for frontend (default: 20)
    --port            Container port (default: 8000 for fastapi, 3000 for frontend)
    --output          Output file path (default: Dockerfile)
    --app-dir         Application directory (default: .)

Examples:
    generate_dockerfile.py --type fastapi --python-version 3.12 --port 8000
    generate_dockerfile.py --type vite --node-version 20 --port 3000
    generate_dockerfile.py --type nextjs --output frontend/Dockerfile
"""

import argparse
import sys
from pathlib import Path

FASTAPI_TEMPLATE = '''# syntax=docker/dockerfile:1
# FastAPI Production Dockerfile
# Built with multi-stage build, non-root user, and healthcheck

FROM python:{python_version}-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc libpq-dev && \\
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:{python_version}-slim

# Create non-root user
RUN groupadd --gid 1000 appgroup && \\
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq5 curl && \\
    rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appgroup {app_dir} ./

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

EXPOSE {port}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
'''

VITE_TEMPLATE = '''# syntax=docker/dockerfile:1
# Vite/React Production Dockerfile
# Multi-stage build with nginx for serving static files

# Build stage
FROM node:{node_version}-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Create non-root user
RUN addgroup -g 1000 appgroup && \\
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Change ownership
RUN chown -R appuser:appgroup /usr/share/nginx/html && \\
    chown -R appuser:appgroup /var/cache/nginx && \\
    chown -R appuser:appgroup /var/log/nginx && \\
    touch /var/run/nginx.pid && \\
    chown -R appuser:appgroup /var/run/nginx.pid

USER appuser

EXPOSE {port}

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost:{port}/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
'''

NEXTJS_TEMPLATE = '''# syntax=docker/dockerfile:1
# Next.js Production Dockerfile
# Optimized standalone output mode

FROM node:{node_version}-alpine AS deps
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build stage
FROM node:{node_version}-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set Next.js to output standalone
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# Production stage
FROM node:{node_version}-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \\
    NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1000 nodejs && \\
    adduser --system --uid 1000 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE {port}

ENV PORT={port}
ENV HOSTNAME="0.0.0.0"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost:{port}/api/health || exit 1

CMD ["node", "server.js"]
'''

NGINX_CONF = '''user appuser;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    server {
        listen {port};
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Handle SPA routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Cache static assets
        location ~* \\.(?:css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }
}
'''

TEMPLATES = {
    'fastapi': FASTAPI_TEMPLATE,
    'vite': VITE_TEMPLATE,
    'nextjs': NEXTJS_TEMPLATE,
}

DEFAULT_PORTS = {
    'fastapi': 8000,
    'vite': 3000,
    'nextjs': 3000,
}


def generate_dockerfile(app_type: str, python_version: str = '3.12',
                        node_version: str = '20', port: int = None,
                        app_dir: str = '.', output: str = 'Dockerfile') -> str:
    """Generate a Dockerfile for the specified application type."""

    if app_type not in TEMPLATES:
        raise ValueError(f"Unknown app type: {app_type}. Choose from: {list(TEMPLATES.keys())}")

    if port is None:
        port = DEFAULT_PORTS[app_type]

    template = TEMPLATES[app_type]

    dockerfile_content = template.format(
        python_version=python_version,
        node_version=node_version,
        port=port,
        app_dir=app_dir,
    )

    return dockerfile_content


def main():
    parser = argparse.ArgumentParser(
        description='Generate optimized Dockerfiles for web applications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--type', required=True, choices=['fastapi', 'vite', 'nextjs'],
                        help='Application type')
    parser.add_argument('--python-version', default='3.12',
                        help='Python version for FastAPI (default: 3.12)')
    parser.add_argument('--node-version', default='20',
                        help='Node version for frontend (default: 20)')
    parser.add_argument('--port', type=int,
                        help='Container port (default: 8000 for fastapi, 3000 for frontend)')
    parser.add_argument('--app-dir', default='.',
                        help='Application directory to copy (default: .)')
    parser.add_argument('--output', default='Dockerfile',
                        help='Output file path (default: Dockerfile)')

    args = parser.parse_args()

    try:
        dockerfile = generate_dockerfile(
            app_type=args.type,
            python_version=args.python_version,
            node_version=args.node_version,
            port=args.port,
            app_dir=args.app_dir,
            output=args.output,
        )

        # Write Dockerfile
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dockerfile)
        print(f"Generated {args.type} Dockerfile: {output_path}")

        # For Vite, also generate nginx.conf
        if args.type == 'vite':
            port = args.port or DEFAULT_PORTS['vite']
            nginx_content = NGINX_CONF.format(port=port)
            nginx_path = output_path.parent / 'nginx.conf'
            nginx_path.write_text(nginx_content)
            print(f"Generated nginx.conf: {nginx_path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
