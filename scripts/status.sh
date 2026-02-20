#!/bin/bash
# Show system status

echo "🏥 Healthcare EHR System Status"
echo "================================"
echo ""

# Backend Status
if pgrep -f "backend/main.py" > /dev/null; then
    echo "✅ Backend: Running"
else
    echo "❌ Backend: Stopped"
fi

# Odoo Status
if pgrep -f "odoo-bin" > /dev/null || pgrep -f "odoo" > /dev/null; then
    echo "✅ Odoo: Running"
else
    echo "❌ Odoo: Stopped"
fi

# Watchers Status
echo ""
echo "Watchers (PM2):"
pm2 status 2>/dev/null || echo "  PM2 not running"

# Vault Summary
echo ""
echo "Vault Summary:"
if [ -d "AI_Employee_Vault" ]; then
    PENDING=$(ls -1 AI_Employee_Vault/Pending_Approval/*.md 2>/dev/null | wc -l)
    DONE=$(ls -1 AI_Employee_Vault/Done/*.md 2>/dev/null | grep $(date +%Y-%m-%d) 2>/dev/null | wc -l)
    echo "  Pending Approval: $PENDING"
    echo "  Done Today: $DONE"
else
    echo "  ⚠️  Vault not found at AI_Employee_Vault/"
fi
