#!/bin/bash
# Script to run only the dashboard

echo "Starting Digital FTE dashboard..."

# Navigate to dashboard directory and start development server
cd dashboard
echo "Starting dashboard on http://localhost:5173..."
npm run dev