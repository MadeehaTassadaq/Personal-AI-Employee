# Odoo Facebook Lead Integration Setup

## Summary of Changes Made

1. Removed Docker-based Odoo configuration from `docker-compose.yml`
2. Removed empty `odoo-addons` directory
3. Created a custom Facebook lead integration module
4. Prepared configuration script for local Odoo

## Facebook Lead Integration Module Features

The `facebook_leads` module includes:
- A custom model to store Facebook leads (`facebook.lead`)
- Views to manage Facebook leads
- Functionality to convert leads to CRM opportunities
- Webhook handler for incoming Facebook lead data

## Next Steps

### 1. Configure Odoo to Recognize Custom Modules
Run the configuration script (you'll need to provide your password):
```bash
sudo /home/madeeha/Documents/Personal-AI-Employee/configure_odoo_custom_addons.sh
```

### 2. Restart Odoo Service
```bash
sudo systemctl restart odoo
```

### 3. Install the Module in Odoo
1. Open your browser and go to http://localhost:8069
2. Log in to Odoo
3. Go to Apps menu
4. Click "Update Apps List"
5. Search for "Facebook Leads Integration"
6. Click "Install"

### 4. Configure Facebook Integration
1. In your Facebook Ads Manager:
   - Create a lead form for your ad campaign
   - Set up a webhook to send leads to your Odoo server
   - The webhook URL will be: `http://YOUR_SERVER_DOMAIN/webhook/facebook_lead`

### 5. Security Considerations
- Change the default admin password in Odoo
- Secure your webhook endpoint with authentication
- Consider using HTTPS for your Odoo instance

## Local vs Docker Comparison

| Aspect | Local Odoo (Used) | Docker Odoo (Removed) |
|--------|-------------------|----------------------|
| Performance | Native speed | Container overhead |
| Resource Usage | Direct access | Isolated resources |
| Configuration | System-wide | Container-specific |
| Development | Direct file access | Volume mapping |
| Maintenance | System packages | Image updates |

## Troubleshooting

If you encounter issues:
1. Check if Odoo is running: `ps aux | grep odoo`
2. Check Odoo logs: `sudo tail -f /var/log/odoo/odoo-server.log`
3. Verify the addons path in your Odoo configuration

## Cleaning Up

If you ever want to remove the Facebook integration:
1. Uninstall the module from Odoo Apps
2. Delete the `/home/madeeha/odoo_custom_addons` directory
3. Restore the original `/etc/odoo/odoo.conf` backup if needed