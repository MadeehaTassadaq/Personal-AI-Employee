# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # === Healthcare Identification ===
    is_patient = fields.Boolean(string='Is Patient', default=False,
                              help='Check if this contact is a patient')
    is_doctor = fields.Boolean(string='Is Doctor', default=False,
                             help='Check if this contact is a doctor/physician')
    medical_record_number = fields.Char(string='Medical Record #',
                                     help='Unique medical record number (MRN)')

    # === Basic Medical Info ===
    date_of_birth = fields.Date(string='Date of Birth',
                               help='Patient date of birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=False,
                       help='Patient age (computed from date of birth)')

    blood_type = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('unknown', 'Unknown')
    ], string='Blood Type', default='unknown',
       help='Patient blood type')

    # === Medical History ===
    allergies = fields.Text(string='Allergies',
                           help='Known allergies (medications, food, environmental)')
    chronic_conditions = fields.Text(string='Chronic Conditions',
                                  help='Chronic medical conditions')
    past_surgeries = fields.Text(string='Past Surgeries',
                                 help='Previous surgical procedures')
    family_history = fields.Text(string='Family Medical History',
                                help='Relevant family medical history')

    # === Female Health ===
    pregnancy_status = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('not_pregnant', 'Not Pregnant'),
        ('pregnant', 'Pregnant'),
        ('high_risk', 'High Risk Pregnancy'),
    ], string='Pregnancy Status', default='not_applicable',
       help='Current pregnancy status')

    last_prenatal_checkup = fields.Date(string='Last Prenatal Checkup',
                                        help='Date of last prenatal visit')
    expected_due_date = fields.Date(string='Expected Due Date',
                                   help='Expected date of delivery')

    # === Risk Assessment ===
    risk_category = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ], string='Risk Category', default='low',
       help='Patient risk category for care management')

    # === Healthcare Contacts ===
    emergency_contact_id = fields.Many2one('res.partner', string='Emergency Contact',
                                          help='Primary emergency contact')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone',
                                        help='Emergency contact phone number')
    primary_physician_id = fields.Many2one('res.partner', string='Primary Physician',
                                           domain=[('is_doctor', '=', True)],
                                           help='Primary care physician')

    # === Insurance ===
    insurance_provider = fields.Char(string='Insurance Provider',
                                    help='Health insurance company name')
    insurance_policy_number = fields.Char(string='Policy Number',
                                        help='Insurance policy/member number')
    insurance_member_id = fields.Char(string='Insurance Member ID',
                                     help='Member ID for insurance claims')

    # === Visit Tracking ===
    last_visit_date = fields.Date(string='Last Visit',
                                  help='Date of last clinic visit')
    next_appointment = fields.Datetime(string='Next Appointment',
                                      help='Next scheduled appointment')
    total_visits = fields.Integer(string='Total Visits', default=0,
                                  help='Total number of visits to the clinic')

    # === Computed Fields ===
    @api.depends('date_of_birth')
    def _compute_age(self):
        """Compute patient age from date of birth."""
        for record in self:
            if record.date_of_birth:
                today = date.today()
                born = record.date_of_birth
                # Calculate age
                age = today.year - born.year - (
                    (today.month, today.day) < (born.month, born.day)
                )
                record.age = age
            else:
                record.age = 0

    @api.model
    def create(self, vals):
        """Generate medical record number if creating a patient."""
        if vals.get('is_patient') and not vals.get('medical_record_number'):
            vals['medical_record_number'] = self._generate_mrn()
        return super(ResPartner, self).create(vals)

    def _generate_mrn(self):
        """Generate unique medical record number."""
        # Format: MRN-YYYY-XXXXX
        import random
        year = date.today().year
        while True:
            mrn = f"MRN-{year}-{random.randint(10000, 99999)}"
            if not self.search([('medical_record_number', '=', mrn)]):
                return mrn

    def write(self, vals):
        """Track visit count when last_visit_date is updated."""
        if vals.get('last_visit_date'):
            for record in self:
                if record.is_patient:
                    vals['total_visits'] = record.total_visits + 1
        return super(ResPartner, self).write(vals)

    def name_get(self):
        """Override name_get to include MRN for patients."""
        result = []
        for record in self:
            name = record.name
            if record.is_patient and record.medical_record_number:
                name = f"{name} ({record.medical_record_number})"
            result.append((record.id, name))
        return result

    @api.constrains('pregnancy_status', 'expected_due_date')
    def _check_pregnancy_dates(self):
        """Validate pregnancy due dates."""
        for record in self:
            if record.pregnancy_status in ['pregnant', 'high_risk']:
                if not record.expected_due_date:
                    raise models.ValidationError(
                        'Expected due date is required for pregnant patients'
                    )
