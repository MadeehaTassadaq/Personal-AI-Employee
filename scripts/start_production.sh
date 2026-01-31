#!/bin/bash
# Production startup script for Digital FTE

set -e  # Exit on any error

echo "🚀 Starting Digital FTE Production System..."

# Change to project directory
cd "$(dirname "$0")/.."

# Set environment variables
export VAULT_PATH="./AI_Employee_Vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DRY_RUN="false"  # Enable real actions for production
export API_PORT="8000"

# Create necessary directories
mkdir -p "$VAULT_PATH"/{Inbox,Needs_Action,Pending_Approval,Approved,Done,Logs,Plans,Audit,.obsidian}
mkdir -p credentials

echo "📁 Ensuring vault structure is complete..."

# Function to start a service in background
start_service() {
    local name=$1
    local cmd=$2
    local log_file="logs/${name}.log"

    echo "⚡ Starting $name..."
    mkdir -p logs
    nohup $cmd > "$log_file" 2>&1 &
    local pid=$!
    echo "$name started with PID: $pid"
    echo "$pid" > "logs/${name}.pid"
    echo "$name: $pid" >> logs/service_pids.txt
}

# Function to stop all services
stop_all_services() {
    echo ""
    echo "🛑 Stopping all services..."

    if [ -f "logs/service_pids.txt" ]; then
        while IFS= read -r line; do
            service_name=$(echo "$line" | cut -d':' -f1)
            pid=$(echo "$line" | cut -d':' -f2)

            if kill -0 "$pid" 2>/dev/null; then
                echo "Stopping $service_name (PID: $pid)..."
                kill "$pid"

                # Wait for graceful shutdown
                for i in {1..10}; do
                    if ! kill -0 "$pid" 2>/dev/null; then
                        break
                    fi
                    sleep 1
                done

                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    echo "Force killing $service_name (PID: $pid)..."
                    kill -9 "$pid" 2>/dev/null
                fi
            fi
        done < logs/service_pids.txt

        rm -f logs/service_pids.txt
    fi

    # Kill any remaining Python processes (be careful!)
    for pid in $(pgrep -f "python.*\(main\|watcher\)"); do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
        fi
    done

    echo "✅ All services stopped."
    exit 0
}

# Set up signal handler for graceful shutdown
trap stop_all_services SIGTERM SIGINT SIGQUIT

# Start the backend API server
start_service "backend" "uvicorn backend.main:app --host 0.0.0.0 --port $API_PORT --reload"

# Wait a moment for backend to start
sleep 5

# Check if backend is running
if ! curl -s http://localhost:$API_PORT/health >/dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi

echo "✅ Backend API server is running on port $API_PORT"

# Start the dashboard (frontend dev server)
if [ -d "dashboard" ] && [ -f "dashboard/package.json" ]; then
    echo "🌐 Starting dashboard..."
    cd dashboard
    if [ -d "node_modules" ]; then
        npm run dev > "../logs/dashboard.log" 2>&1 &
    else
        echo "⚠️  Dashboard node_modules not found, installing..."
        npm install > ../logs/npm_install.log 2>&1
        npm run dev > "../logs/dashboard.log" 2>&1 &
    fi
    DASHBOARD_PID=$!
    echo "dashboard: $DASHBOARD_PID" >> ../logs/service_pids.txt
    cd ..
    echo "✅ Dashboard started"
fi

# Start watchers separately (they run continuously)
echo "👀 Starting watchers in background..."
nohup ./scripts/run_watchers.sh > logs/watchers.log 2>&1 &
WATCHERS_PID=$!
echo "watchers: $WATCHERS_PID" >> logs/service_pids.txt
echo "✅ Watchers started"

echo ""
echo "🎉 Digital FTE Production System is running!"
echo ""
echo "📊 Dashboard: http://localhost:3000 (if started)"
echo "🔌 API Server: http://localhost:$API_PORT"
echo "📁 Vault: $VAULT_PATH"
echo ""
echo "📋 Services running:"
if [ -f "logs/service_pids.txt" ]; then
    cat logs/service_pids.txt
fi
echo ""
echo "💡 Press Ctrl+C to shut down all services gracefully"
echo ""

# Monitor services
while true; do
    if [ -f "logs/service_pids.txt" ]; then
        while IFS= read -r line; do
            service_name=$(echo "$line" | cut -d':' -f1)
            pid=$(echo "$line" | cut -d':' -f2)

            if ! kill -0 "$pid" 2>/dev/null; then
                echo "⚠️  Service $service_name (PID: $pid) has died"
                if [ "$service_name" = "backend" ]; then
                    echo "❌ Backend died, shutting down all services"
                    stop_all_services
                fi
            fi
        done < logs/service_pids.txt
    fi

    sleep 10
done