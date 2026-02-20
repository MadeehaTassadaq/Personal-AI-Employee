#!/bin/bash
# Start entire Healthcare EHR system

cd "$(dirname "$0")/.."

echo "🏥 Starting Healthcare EHR System..."

# Load environment
if [ -f "backend/.env" ]; then
    export $(cat backend/.env | grep -v '^#' | xargs)
else
    echo "Note: backend/.env not found"
fi

# Start FastAPI Backend
echo "Starting FastAPI Backend..."
cd backend
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python main.py &
elif command -v uv &> /dev/null; then
    uv run python main.py &
else
    python3 main.py &
fi
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start Watchers via PM2
echo "Starting Watchers..."
pm2 start watchers/*.py --interpreter python3 --name "healthcare-watchers" 2>/dev/null || pm2 restart healthcare-watchers

echo "✅ System Started"
echo "   Backend PID: $BACKEND_PID"
echo "   Watchers: pm2 status"
echo ""
echo "Check logs:"
echo "   Backend: Check console output"
echo "   Watchers: pm2 logs"
echo ""
echo "API available at: http://localhost:${API_PORT:-8000}"
