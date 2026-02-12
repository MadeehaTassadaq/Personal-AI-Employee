#!/usr/bin/env python3
"""
Facebook Lead Integration Setup for Local Odoo
This script helps configure Facebook lead capture in your local Odoo 19 installation.
"""

import os
import sys
import requests
import json
from pathlib import Path

def check_odoo_running():
    """Check if Odoo is running locally"""
    try:
        response = requests.get("http://localhost:8069/web", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_facebook_lead_module():
    """Create a basic structure for Facebook lead capture module"""

    # Create the custom addons directory if it doesn't exist
    addons_dir = Path.home() / "odoo_custom_addons"
    addons_dir.mkdir(exist_ok=True)

    # Create facebook_leads module directory
    fb_module_dir = addons_dir / "facebook_leads"
    fb_module_dir.mkdir(exist_ok=True)

    # Create __manifest__.py
    manifest_content = '''{
    "name": "Facebook Leads Integration",
    "summary": "Capture leads from Facebook campaigns",
    "description": """
    This module integrates with Facebook to capture leads from campaigns
    and store them as opportunities in Odoo CRM.
    """,
    "author": "Your Company",
    "website": "https://www.yourcompany.com",
    "category": "Marketing",
    "version": "1.0.0",
    "depends": ["crm", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "views/facebook_lead_views.xml",
        "views/menu_items.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
'''

    with open(fb_module_dir / "__manifest__.py", "w") as f:
        f.write(manifest_content)

    # Create __init__.py
    with open(fb_module_dir / "__init__.py", "w") as f:
        f.write("from . import models\n")

    # Create models directory
    models_dir = fb_module_dir / "models"
    models_dir.mkdir(exist_ok=True)

    # Create __init__.py in models
    with open(models_dir / "__init__.py", "w") as f:
        f.write("from . import facebook_lead\n")

    # Create the main model file
    model_content = '''from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class FacebookLead(models.Model):
    _name = 'facebook.lead'
    _description = 'Facebook Lead'
    _order = 'create_date desc'

    name = fields.Char('Lead Name', required=True)
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    facebook_lead_id = fields.Char('Facebook Lead ID', required=True, unique=True)
    ad_campaign_name = fields.Char('Ad Campaign Name')
    ad_form_name = fields.Char('Ad Form Name')
    submission_date = fields.Datetime('Submission Date')
    converted_opportunity_id = fields.Many2one('crm.lead', 'Converted Opportunity')
    state = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('converted', 'Converted'),
        ('lost', 'Lost')
    ], default='new')

    def convert_to_opportunity(self):
        """Convert Facebook lead to CRM opportunity"""
        for lead in self:
            opportunity = self.env['crm.lead'].create({
                'name': lead.name,
                'email_from': lead.email,
                'phone': lead.phone,
                'type': 'opportunity',
                'description': f'Converted from Facebook lead {lead.facebook_lead_id}',
                'source_id': self.env.ref('crm.source_facebook', raise_if_not_found=False),
            })
            lead.converted_opportunity_id = opportunity.id
            lead.state = 'converted'

    @api.model
    def create_from_facebook_webhook(self, payload):
        """Create Facebook lead from webhook payload"""
        lead_data = {
            'name': payload.get('full_name', ''),
            'email': payload.get('email', ''),
            'phone': payload.get('phone_number', ''),
            'facebook_lead_id': payload['id'],
            'ad_campaign_name': payload.get('ad_campaign_name', ''),
            'ad_form_name': payload.get('form_name', ''),
            'submission_date': fields.Datetime.now(),
        }

        existing_lead = self.search([('facebook_lead_id', '=', payload['id'])])
        if existing_lead:
            return existing_lead

        return self.create(lead_data)
'''

    with open(models_dir / "facebook_lead.py", "w") as f:
        f.write(model_content)

    # Create security directory
    security_dir = fb_module_dir / "security"
    security_dir.mkdir(exist_ok=True)

    # Create ir.model.access.csv
    with open(security_dir / "ir.model.access.csv", "w") as f:
        f.write('''id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_facebook_lead_user,access_facebook_lead,model_facebook_lead,base.group_user,1,1,1,1
access_facebook_lead_public,access_facebook_lead,model_facebook_lead,base.group_public,1,0,0,0
''')

    # Create views directory
    views_dir = fb_module_dir / "views"
    views_dir.mkdir(exist_ok=True)

    # Create menu_items.xml
    menu_content = '''<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <menuitem id="facebook_leads_menu_root" name="Facebook Leads" sequence="5"/>

    <menuitem id="facebook_leads_menu"
              name="Facebook Leads"
              parent="facebook_leads_menu_root"
              sequence="10"/>

    <menuitem id="facebook_leads_submenu"
              name="Leads"
              parent="facebook_leads_menu"
              action="action_facebook_leads"
              sequence="10"/>
</odoo>
'''

    with open(views_dir / "menu_items.xml", "w") as f:
        f.write(menu_content)

    print(f"Facebook lead module created at: {fb_module_dir}")
    print("\nTo use this module:")
    print("1. Add this path to your Odoo configuration file:")
    print(f"   addons_path = /path/to/your/addons,/home/{os.getenv('USER')}/odoo_custom_addons")
    print("2. Restart your Odoo server")
    print("3. Go to Apps > Update Apps List")
    print("4. Search for 'Facebook Leads Integration' and install")
    print("5. Configure Facebook webhook to point to your server")

if __name__ == "__main__":
    print("Checking if Odoo is running...")
    if check_odoo_running():
        print("✓ Odoo is running on localhost:8069")
    else:
        print("⚠ Odoo does not appear to be running on localhost:8069")
        print("Please start your local Odoo server before proceeding.")
        sys.exit(1)

    print("\nCreating Facebook integration module...")
    create_facebook_lead_module()

    print("\nSetup complete! Follow the instructions above to complete the integration.")