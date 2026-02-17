# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # === Healthcare Fields ===
    is_patient = fields.Boolean(string='Patient', default=False)
    is_doctor = fields.Boolean(string='Doctor', default=False)

    # === Patient Information ===
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=False)
    blood_type = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('unknown', 'Unknown')
    ], string='Blood Type', default='unknown')

    allergies = fields.Text(string='Allergies')
    chronic_conditions = fields.Text(string='Chronic Conditions')
    past_surgeries = fields.Text(string='Past Surgeries')
    family_history = fields.Text(string='Family History')

    # === Women's Health ===
    pregnancy_status = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('not_pregnant', 'Not Pregnant'),
        ('pregnant', 'Pregnant'),
        ('high_risk', 'High Risk Pregnancy')
    ], string='Pregnancy Status', default='not_applicable')

    last_prenatal_checkup = fields.Date(string='Last Prenatal Checkup')
    expected_due_date = fields.Date(string='Expected Due Date')

    # === Risk & Insurance ===
    risk_category = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Risk Category', default='low')

    insurance_provider = fields.Char(string='Insurance Provider')
    insurance_policy_number = fields.Char(string='Policy Number')
    insurance_member_id = fields.Char(string='Member ID')

    # === Healthcare Specific ===
    medical_record_number = fields.Char(string='Medical Record #', compute='_compute_mrn', store=True, copy=False)

    primary_physician_id = fields.Many2one('res.partner', string='Primary Physician', domain=[('is_doctor', '=', True)])

    emergency_contact_id = fields.Many2one('res.partner', string='Emergency Contact')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')

    # === Visit Statistics ===
    last_visit_date = fields.Date(string='Last Visit Date')
    next_appointment = fields.Datetime(string='Next Appointment')
    total_visits = fields.Integer(string='Total Visits', default=0)

    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                record.age = (fields.Date.today() - record.date_of_birth).days // 365

    @api.depends('name')
    def _compute_mrn(self):
        for record in self:
            if record.is_patient:
                record.medical_record_number = f'MRN{record.id:06d}'
            else:
                record.medical_record_number = False
