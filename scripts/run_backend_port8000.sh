#!/bin/bash
# Script to run the backend API on port 8000 (matches Vite proxy config)

echo "Starting Digital FTE backend on port 8000..."

# Change to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export VAULT_PATH="./AI_Employee_Vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start backend API on port 8000
echo "Starting backend API on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000