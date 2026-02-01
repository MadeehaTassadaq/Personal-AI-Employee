#!/bin/bash
# Test script to verify Digital FTE system functionality

echo "Digital FTE System Verification Tests"
echo "====================================="

# Test 1: Check if required directories exist
echo "Test 1: Checking required directories..."
if [ -d "./AI_Employee_Vault" ]; then
    echo "✓ AI_Employee_Vault directory exists"
else
    echo "✗ AI_Employee_Vault directory missing"
fi

for dir in Inbox Needs_Action Pending_Approval Approved Done Logs Plans; do
    if [ -d "./AI_Employee_Vault/$dir" ]; then
        echo "✓ $dir directory exists"
    else
        echo "✗ $dir directory missing"
    fi
done

# Test 2: Check if dashboard exists and is readable
echo -e "\nTest 2: Checking dashboard..."
if [ -f "./AI_Employee_Vault/Dashboard.md" ]; then
    echo "✓ Dashboard.md exists"
    lines=$(wc -l < "./AI_Employee_Vault/Dashboard.md")
    echo "  Lines in dashboard: $lines"
else
    echo "✗ Dashboard.md missing"
fi

# Test 3: Check if environment file is properly configured
echo -e "\nTest 3: Checking environment configuration..."
if [ -f "./.env" ]; then
    echo "✓ .env file exists"
    if grep -q "VAULT_PATH=./AI_Employee_Vault" .env; then
        echo "✓ VAULT_PATH is correctly configured"
    else
        echo "✗ VAULT_PATH may be misconfigured"
    fi
else
    echo "✗ .env file missing"
fi

# Test 4: Check if Python modules exist
echo -e "\nTest 4: Checking Python modules..."
modules=("backend/main.py" "watchers/file_watcher.py" "backend/api/approvals.py")
for module in "${modules[@]}"; do
    if [ -f "./$module" ]; then
        echo "✓ $module exists"
    else
        echo "✗ $module missing"
    fi
done

# Test 5: Check if scripts exist
echo -e "\nTest 5: Checking scripts..."
scripts=("scripts/run_watchers.sh" "scripts/setup_uv.sh")
for script in "${scripts[@]}"; do
    if [ -f "./$script" ]; then
        echo "✓ $script exists"
        if [ -x "./$script" ]; then
            echo "  $script is executable"
        else
            echo "  $script is NOT executable"
        fi
    else
        echo "✗ $script missing"
    fi
done

# Test 6: Count tasks in each folder
echo -e "\nTest 6: Counting tasks in each folder..."
folders=("Inbox" "Needs_Action" "Pending_Approval" "Approved" "Done")
for folder in "${folders[@]}"; do
    if [ -d "./AI_Employee_Vault/$folder" ]; then
        count=$(find "./AI_Employee_Vault/$folder" -name "*.md" -type f | wc -l)
        echo "  $folder: $count tasks"
    else
        echo "  $folder: N/A (directory missing)"
    fi
done

echo -e "\nSystem verification complete!"
echo "To run the system with uv, use: ./scripts/setup_uv.sh"