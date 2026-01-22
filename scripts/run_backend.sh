#!/bin/bash
# Script to run only the backend API

echo "Starting Digital FTE backend..."

# Set environment variables
export VAULT_PATH="./vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start backend API
echo "Starting backend API on port 8000..."
cd backend
uvicorn api:app --host 0.0.0.0 --port 8000