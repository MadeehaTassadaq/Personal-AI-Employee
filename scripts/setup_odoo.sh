#!/bin/bash
# Odoo Setup Script for Personal AI Employee
# This script sets up Odoo Community Edition via Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Odoo Setup..."
echo "Project directory: $PROJECT_DIR"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Navigate to project directory
cd "$PROJECT_DIR"

# Start containers
echo "📦 Starting Odoo and PostgreSQL containers..."
# Use sudo if not running as root
if [ "$(id -u)" -ne 0 ]; then
    sudo docker compose up -d
else
    docker compose up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for Odoo to start (this may take 30-60 seconds)..."
sleep 10

# Check if containers are running
DOCKER_CMD="docker compose"
if [ "$(id -u)" -ne 0 ]; then
    DOCKER_CMD="sudo docker compose"
fi

if $DOCKER_CMD ps | grep -q "odoo.*running"; then
    echo "✅ Odoo container is running"
else
    echo "⚠️  Waiting for Odoo container to fully start..."
    sleep 20
fi

if $DOCKER_CMD ps | grep -q "db.*running"; then
    echo "✅ PostgreSQL container is running"
else
    echo "⚠️  Waiting for PostgreSQL container to fully start..."
    sleep 10
fi

# Check Odoo health
echo "🔍 Checking Odoo availability..."
MAX_ATTEMPTS=30
ATTEMPT=1
while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8069 | grep -q "200\|303"; then
        echo "✅ Odoo is responding at http://localhost:8069"
        break
    fi
    echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting for Odoo..."
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "⚠️  Odoo may still be starting. Check http://localhost:8069 manually."
fi

echo ""
echo "=========================================="
echo "✅ Odoo Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Open http://localhost:8069 in your browser"
echo "2. Create database: ai_employee_db"
echo "3. Set admin email and password"
echo "4. Install modules: Invoicing, Expenses, Contacts"
echo "5. Update .env with your admin credentials"
echo ""
echo "After setup, update these in .env:"
echo "  ODOO_URL=http://localhost:8069"
echo "  ODOO_DB=ai_employee_db"
echo "  ODOO_USERNAME=admin"
echo "  ODOO_PASSWORD=<your-password>"
echo ""
