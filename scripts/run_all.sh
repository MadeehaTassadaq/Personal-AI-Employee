#!/bin/bash
# Script to run all services for Digital FTE

echo "Starting Digital FTE services..."

# Change to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export VAULT_PATH="./vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start backend API in background
echo "Starting backend API..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start file watcher in background
echo "Starting file watcher..."
python watchers/file_watcher.py ./vault &
WATCHER_PID=$!

# Start dashboard in background
echo "Starting dashboard..."
cd dashboard
npm run dev &
DASHBOARD_PID=$!
cd ..

echo "All services started!"
echo "Backend: http://localhost:8000"
echo "Dashboard: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all processes
wait $BACKEND_PID $WATCHER_PID $DASHBOARD_PID