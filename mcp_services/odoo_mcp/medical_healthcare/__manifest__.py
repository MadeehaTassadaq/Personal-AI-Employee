# -*- coding: utf-8 -*-
{
    'name': 'Healthcare Management',
    'version': '1.0.0',
    'category': 'Healthcare',
    'summary': 'Patient and healthcare management for medical practices',
    'description': '''
        Healthcare Management Module
        ============================

        Comprehensive healthcare management for medical practices, clinics, and hospitals.

        Features:
        * Patient profiles with medical history
        * Appointment scheduling and reminders
        * Vitals tracking
        * Patient billing integration
        * Risk category management
        * Pregnancy status tracking
        * Allergies and chronic conditions
    ''',
    'author': 'Digital FTE',
    'website': 'https://github.com/digital-fte',
    'depends': [
        'base',
        'contacts',
        'calendar',
        'account',
    ],
    'data': [
        'security/healthcare_security.xml',
        'security/ir.model.access.csv',
        'views/partner_views.xml',
        'views/appointment_views.xml',
        'views/vitals_views.xml',
        'views/menu_items.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'images': [],
}
