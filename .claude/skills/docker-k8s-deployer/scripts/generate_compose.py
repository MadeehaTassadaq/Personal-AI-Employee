#!/usr/bin/env python3
"""
Docker Compose Generator - Creates docker-compose.yml for multi-service stacks

Usage:
    generate_compose.py --services <service1,service2,...> [options]

Options:
    --services         Comma-separated service types: backend, frontend, db, redis (required)
    --backend-port     Backend port (default: 8000)
    --frontend-port    Frontend port (default: 3000)
    --db-type          Database type: postgres, mysql (default: postgres)
    --output           Output file path (default: docker-compose.yml)
    --project-name     Project name for container naming

Examples:
    generate_compose.py --services backend,frontend,db
    generate_compose.py --services backend,db,redis --backend-port 8080
    generate_compose.py --services backend,frontend --project-name myapp
"""

import argparse
import sys
from pathlib import Path
import yaml


def generate_backend_service(port: int, depends_on: list = None) -> dict:
    """Generate backend service configuration."""
    service = {
        'build': {
            'context': './backend',
            'dockerfile': 'Dockerfile',
        },
        'ports': [f'{port}:{port}'],
        'environment': [
            'DATABASE_URL=${DATABASE_URL}',
            'SECRET_KEY=${SECRET_KEY}',
            'DEBUG=${DEBUG:-false}',
        ],
        'healthcheck': {
            'test': ['CMD', 'curl', '-f', f'http://localhost:{port}/health'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3,
            'start_period': '10s',
        },
        'restart': 'unless-stopped',
        'networks': ['app-network'],
    }
    if depends_on:
        service['depends_on'] = {
            svc: {'condition': 'service_healthy'} for svc in depends_on
        }
    return service


def generate_frontend_service(port: int, backend_port: int) -> dict:
    """Generate frontend service configuration."""
    return {
        'build': {
            'context': './frontend',
            'dockerfile': 'Dockerfile',
        },
        'ports': [f'{port}:{port}'],
        'environment': [
            f'NEXT_PUBLIC_API_URL=http://backend:{backend_port}',
        ],
        'healthcheck': {
            'test': ['CMD', 'wget', '--no-verbose', '--tries=1', '--spider', f'http://localhost:{port}/'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3,
            'start_period': '10s',
        },
        'depends_on': {
            'backend': {'condition': 'service_healthy'},
        },
        'restart': 'unless-stopped',
        'networks': ['app-network'],
    }


def generate_postgres_service() -> dict:
    """Generate PostgreSQL service configuration."""
    return {
        'image': 'postgres:16-alpine',
        'environment': [
            'POSTGRES_USER=${POSTGRES_USER:-postgres}',
            'POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}',
            'POSTGRES_DB=${POSTGRES_DB:-app}',
        ],
        'volumes': [
            'postgres-data:/var/lib/postgresql/data',
        ],
        'healthcheck': {
            'test': ['CMD-SHELL', 'pg_isready -U ${POSTGRES_USER:-postgres}'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 5,
            'start_period': '10s',
        },
        'restart': 'unless-stopped',
        'networks': ['app-network'],
    }


def generate_mysql_service() -> dict:
    """Generate MySQL service configuration."""
    return {
        'image': 'mysql:8.0',
        'environment': [
            'MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-rootpassword}',
            'MYSQL_USER=${MYSQL_USER:-app}',
            'MYSQL_PASSWORD=${MYSQL_PASSWORD:-password}',
            'MYSQL_DATABASE=${MYSQL_DATABASE:-app}',
        ],
        'volumes': [
            'mysql-data:/var/lib/mysql',
        ],
        'healthcheck': {
            'test': ['CMD', 'mysqladmin', 'ping', '-h', 'localhost'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 5,
            'start_period': '30s',
        },
        'restart': 'unless-stopped',
        'networks': ['app-network'],
    }


def generate_redis_service() -> dict:
    """Generate Redis service configuration."""
    return {
        'image': 'redis:7-alpine',
        'command': 'redis-server --appendonly yes',
        'volumes': [
            'redis-data:/data',
        ],
        'healthcheck': {
            'test': ['CMD', 'redis-cli', 'ping'],
            'interval': '10s',
            'timeout': '5s',
            'retries': 5,
        },
        'restart': 'unless-stopped',
        'networks': ['app-network'],
    }


def generate_compose(services: list, backend_port: int = 8000,
                     frontend_port: int = 3000, db_type: str = 'postgres') -> dict:
    """Generate complete docker-compose configuration."""

    compose = {
        'services': {},
        'networks': {
            'app-network': {
                'driver': 'bridge',
            },
        },
        'volumes': {},
    }

    depends_on = []

    # Add database first if requested
    if 'db' in services:
        if db_type == 'postgres':
            compose['services']['db'] = generate_postgres_service()
            compose['volumes']['postgres-data'] = {}
        elif db_type == 'mysql':
            compose['services']['db'] = generate_mysql_service()
            compose['volumes']['mysql-data'] = {}
        depends_on.append('db')

    # Add Redis if requested
    if 'redis' in services:
        compose['services']['redis'] = generate_redis_service()
        compose['volumes']['redis-data'] = {}
        depends_on.append('redis')

    # Add backend
    if 'backend' in services:
        compose['services']['backend'] = generate_backend_service(
            port=backend_port,
            depends_on=depends_on if depends_on else None
        )

    # Add frontend
    if 'frontend' in services:
        compose['services']['frontend'] = generate_frontend_service(
            port=frontend_port,
            backend_port=backend_port
        )

    return compose


def main():
    parser = argparse.ArgumentParser(
        description='Generate docker-compose.yml for multi-service stacks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--services', required=True,
                        help='Comma-separated services: backend,frontend,db,redis')
    parser.add_argument('--backend-port', type=int, default=8000,
                        help='Backend port (default: 8000)')
    parser.add_argument('--frontend-port', type=int, default=3000,
                        help='Frontend port (default: 3000)')
    parser.add_argument('--db-type', choices=['postgres', 'mysql'], default='postgres',
                        help='Database type (default: postgres)')
    parser.add_argument('--output', default='docker-compose.yml',
                        help='Output file path (default: docker-compose.yml)')
    parser.add_argument('--project-name',
                        help='Project name for container naming')

    args = parser.parse_args()

    try:
        services = [s.strip() for s in args.services.split(',')]

        # Validate services
        valid_services = {'backend', 'frontend', 'db', 'redis'}
        invalid = set(services) - valid_services
        if invalid:
            print(f"Error: Invalid services: {invalid}. Valid: {valid_services}", file=sys.stderr)
            return 1

        compose = generate_compose(
            services=services,
            backend_port=args.backend_port,
            frontend_port=args.frontend_port,
            db_type=args.db_type,
        )

        # Add project name if specified
        if args.project_name:
            compose = {'name': args.project_name, **compose}

        # Write to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

        print(f"Generated docker-compose.yml: {output_path}")
        print(f"Services: {', '.join(compose['services'].keys())}")

        # Print .env template
        print("\nCreate .env file with:")
        print("DATABASE_URL=postgresql://postgres:postgres@db:5432/app")
        print("SECRET_KEY=your-secret-key")
        if 'db' in services and args.db_type == 'postgres':
            print("POSTGRES_USER=postgres")
            print("POSTGRES_PASSWORD=postgres")
            print("POSTGRES_DB=app")
        elif 'db' in services and args.db_type == 'mysql':
            print("MYSQL_ROOT_PASSWORD=rootpassword")
            print("MYSQL_USER=app")
            print("MYSQL_PASSWORD=password")
            print("MYSQL_DATABASE=app")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
