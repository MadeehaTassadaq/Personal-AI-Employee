#!/bin/bash
# Setup script to use uv package manager with the Digital FTE project

set -e  # Exit on any error

echo "Setting up Digital FTE project with uv package manager..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    pip install uv
fi

echo "Using uv to install project dependencies..."
uv sync

echo "Digital FTE project setup complete!"
echo ""
echo "Available commands:"
echo "  uv run python -m backend.main          # Start backend API server"
echo "  uv run python -m watchers.file_watcher ./AI_Employee_Vault  # Start file watcher"
echo "  uv run python -m scripts/run_watchers.sh                 # Start all watchers"
echo "  uv run pytest                                               # Run tests"
echo ""

# If called with 'start' argument, start the backend
if [ "$1" = "start" ]; then
    echo "Starting backend server..."
    uv run python -m backend.main
fi