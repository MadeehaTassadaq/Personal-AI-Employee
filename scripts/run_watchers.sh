#!/bin/bash
# Script to run all watchers

echo "Starting Digital FTE watchers..."

# Set environment variables
# Change to project directory
cd "$(dirname "$0")/.."

# Set environment variables
export VAULT_PATH="./AI_Employee_Vault"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start all watchers
echo "Starting file watcher..."
python3 -m watchers.file_watcher ./AI_Employee_Vault &
FILE_WATCHER_PID=$!

echo "Starting Gmail watcher..."
python3 -m watchers.gmail_watcher ./AI_Employee_Vault &
GMAIL_WATCHER_PID=$!

echo "Starting WhatsApp watcher..."
python3 -m watchers.whatsapp_watcher ./AI_Employee_Vault &
WHATSAPP_WATCHER_PID=$!

echo "Starting LinkedIn watcher..."
python3 -m watchers.linkedin_watcher ./AI_Employee_Vault &
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