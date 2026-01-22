#!/bin/bash
# Script to run all watchers

echo "Starting Digital FTE watchers..."

# Set environment variables
export VAULT_PATH="./vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start all watchers
echo "Starting file watcher..."
python watchers/file_watcher.py ./vault &
FILE_WATCHER_PID=$!

echo "Starting Gmail watcher..."
python watchers/gmail_watcher.py ./vault &
GMAIL_WATCHER_PID=$!

echo "Starting WhatsApp watcher..."
python watchers/whatsapp_watcher.py ./vault &
WHATSAPP_WATCHER_PID=$!

echo "Starting LinkedIn watcher..."
python watchers/linkedin_watcher.py ./vault &
LINKEDIN_WATCHER_PID=$!

echo "All watchers started!"
echo "File watcher PID: $FILE_WATCHER_PID"
echo "Gmail watcher PID: $GMAIL_WATCHER_PID"
echo "WhatsApp watcher PID: $WHATSAPP_WATCHER_PID"
echo "LinkedIn watcher PID: $LINKEDIN_WATCHER_PID"
echo ""
echo "Press Ctrl+C to stop all watchers"
echo ""

# Wait for all processes
wait $FILE_WATCHER_PID $GMAIL_WATCHER_PID $WHATSAPP_WATCHER_PID $LINKEDIN_WATCHER_PID