#!/bin/bash
# Script to run all watchers with proper process management

echo "Starting Digital FTE watchers..."

# Change to project directory
cd "$(dirname "$0")/.."

# Set environment variables
export VAULT_PATH="./AI_Employee_Vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DRY_RUN="false"  # Enable real actions by default

# Array to hold PIDs
PIDS=()

# Function to start a watcher and capture PID
start_watcher() {
    local name=$1
    local module=$2
    local path=$3

    echo "Starting $name..."
    python3 -m "$module" "$path" &
    local pid=$!
    PIDS+=($pid)
    echo "$name PID: $pid"
    export "${name^^}_PID=$pid"  # Convert to uppercase and set as env var
}

# Start all watchers
start_watcher "file_watcher" "watchers.file_watcher" "./AI_Employee_Vault"
sleep 2  # Small delay between startups to avoid resource conflicts

start_watcher "gmail_watcher" "watchers.gmail_watcher" "./AI_Employee_Vault"
sleep 2

start_watcher "whatsapp_watcher" "watchers.whatsapp_watcher" "./AI_Employee_Vault"
sleep 2

start_watcher "linkedin_watcher" "watchers.linkedin_watcher" "./AI_Employee_Vault"
sleep 2

echo "All watchers started!"

# Function to handle shutdown
cleanup() {
    echo ""
    echo "Shutting down watchers..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping process $pid"
            kill "$pid"
        fi
    done

    # Wait a moment for graceful shutdown
    sleep 2

    # Force kill any remaining processes
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Force killing process $pid"
            kill -9 "$pid" 2>/dev/null
        fi
    done

    echo "All watchers stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT SIGQUIT

echo "Press Ctrl+C to stop all watchers"
echo ""

# Wait for all processes with error handling
while true; do
    all_alive=true
    for pid in "${PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "Process $pid has died"
            all_alive=false
            break
        fi
    done

    if [ "$all_alive" = false ]; then
        echo "One or more watchers died. Restarting..."
        cleanup
    fi

    sleep 5
done