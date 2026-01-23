#!/bin/bash
# Script to run only the backend API

echo "Starting Digital FTE backend..."

# Change to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export VAULT_PATH="./vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start backend API
echo "Starting backend API on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000