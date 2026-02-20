#!/bin/bash
# Stop entire Healthcare EHR system

echo "🛑 Stopping Healthcare EHR System..."

# Stop PM2 watchers
pm2 stop healthcare-watchers 2>/dev/null
pm2 delete healthcare-watchers 2>/dev/null

# Stop Backend (find and kill)
pkill -f "backend/main.py" 2>/dev/null || echo "Backend not running"

echo "✅ System Stopped"
