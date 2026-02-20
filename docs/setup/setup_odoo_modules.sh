#!/bin/bash
# Setup script to configure Odoo custom modules path

set -e

echo "================================"
echo "Odoo Custom Modules Setup"
echo "================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ODOO_MODULES_DIR="$PROJECT_DIR/odoo_custom_modules"
ODOO_CONF="/etc/odoo/odoo.conf"

echo "Project directory: $PROJECT_DIR"
echo "Odoo modules directory: $ODOO_MODULES_DIR"
echo ""

# Check if modules directory exists
if [ ! -d "$ODOO_MODULES_DIR" ]; then
    echo "ERROR: Odoo modules directory not found: $ODOO_MODULES_DIR"
    exit 1
fi

echo "Found modules:"
ls -la "$ODOO_MODULES_DIR"
echo ""

# Check if medical_healthcare module exists
if [ ! -d "$ODOO_MODULES_DIR/medical_healthcare" ]; then
    echo "ERROR: medical_healthcare module not found"
    exit 1
fi

echo "✓ medical_healthcare module found"
echo ""

# Backup Odoo config
echo "Backing up Odoo configuration..."
sudo cp "$ODOO_CONF" "${ODOO_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✓ Backup created"
echo ""

# Create symlink in Odoo addons directory
ODOO_ADDONS_DIR="/usr/lib/python3/dist-packages/odoo/addons"
echo "Creating symlink in Odoo addons directory: $ODOO_ADDONS_DIR"

# Remove old symlink if exists
if [ -L "$ODOO_ADDONS_DIR/medical_healthcare" ]; then
    sudo rm "$ODOO_ADDONS_DIR/medical_healthcare"
    echo "✓ Removed old symlink"
fi

# Create new symlink
sudo ln -sf "$ODOO_MODULES_DIR/medical_healthcare" "$ODOO_ADDONS_DIR/medical_healthcare"
echo "✓ Created symlink: $ODOO_ADDONS_DIR/medical_healthcare -> $ODOO_MODULES_DIR/medical_healthcare"
echo ""

# Update addons_path in odoo.conf
echo "Updating Odoo addons_path in config..."

# Check if addons_path line exists
if sudo grep -q "^addons_path" "$ODOO_CONF"; then
    # Check if our path is already there
    if sudo grep -q "$ODOO_MODULES_DIR" "$ODOO_CONF"; then
        echo "✓ Path already configured in odoo.conf"
    else
        # Add the path to addons_path
        sudo sed -i "s|^addons_path = \(.*\)|addons_path = \1,$ODOO_MODULES_DIR|" "$ODOO_CONF"
        echo "✓ Added to odoo.conf"
    fi
else
    # Add new addons_path line
    echo "addons_path = $ODOO_ADDONS_DIR,$ODOO_MODULES_DIR" | sudo tee -a "$ODOO_CONF" > /dev/null
    echo "✓ Added addons_path to odoo.conf"
fi
echo ""

# Fix permissions
echo "Setting proper permissions..."
sudo chown -R odoo:odoo "$ODOO_MODULES_DIR"
sudo chmod -R 755 "$ODOO_MODULES_DIR"
echo "✓ Permissions fixed"
echo ""

# Restart Odoo
echo "Restarting Odoo..."
sudo systemctl restart odoo
sleep 3

# Check if Odoo started
if sudo systemctl is-active --quiet odoo; then
    echo "✓ Odoo restarted successfully"
else
    echo "✗ Odoo failed to start!"
    echo "Check logs: sudo journalctl -u odoo -n 50"
    exit 1
fi
echo ""

# Verify symlink
echo "Verifying symlink..."
if [ -L "$ODOO_ADDONS_DIR/medical_healthcare" ]; then
    echo "✓ Symlink exists: $(ls -la $ODOO_ADDONS_DIR/medical_healthcare)"
else
    echo "✗ Symlink not found!"
    exit 1
fi
echo ""

echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Module location: $ODOO_ADDONS_DIR/medical_healthcare"
echo ""
echo "Next steps to upgrade/install the module:"
echo ""
echo "1. Open Odoo: http://localhost:8069"
echo "2. Login as admin"
echo "3. Go to Apps menu"
echo "4. Click 'Update Apps List' (top menu)"
echo "5. Remove 'Apps' filter to see all modules"
echo "6. Search for 'Healthcare Management'"
echo "7. Click Upgrade (if installed) or Install (if not)"
echo ""
echo "Or check Odoo logs:"
echo "  sudo tail -f /var/log/odoo/odoo-server.log"
echo ""
echo "To check if module is loaded:"
echo "  curl -s http://localhost:8000/api/healthcare/patients"
