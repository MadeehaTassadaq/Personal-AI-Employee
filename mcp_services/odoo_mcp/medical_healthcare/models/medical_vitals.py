# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MedicalVitals(models.Model):
    _name = 'medical.vitals'
    _description = 'Patient Vitals'
    _order = 'date_taken desc'

    # === Relationships ===
    patient_id = fields.Many2one('res.partner', string='Patient',
                                required=True, ondelete='cascade',
                                domain=[('is_patient', '=', True)],
                                tracking=True)
    appointment_id = fields.Many2one('medical.appointment', string='Appointment',
                                       help='Associated appointment if any')
    recorded_by_id = fields.Many2one('res.users', string='Recorded By',
                                     default=lambda self: self.env.user,
                                     help='User who recorded these vitals')

    # === Timestamp ===
    date_taken = fields.Datetime(string='Date & Time',
                                 required=True,
                                 default=fields.Datetime.now,
                                 help='When vitals were recorded')

    # === Vital Signs ===
    # Temperature
    temperature = fields.Float(string='Temperature (°C)',
                              digits=(3, 1),
                              help='Body temperature in Celsius')
    temperature_method = fields.Selection([
        ('oral', 'Oral'),
        ('rectal', 'Rectal'),
        ('axillary', 'Axillary'),
        ('temporal', 'Temporal'),
        ('ear', 'Ear'),
    ], string='Temperature Method',
       help='Method used to measure temperature')

    # Blood Pressure
    blood_pressure_systolic = fields.Integer(string='BP Systolic',
                                           help='Systolic blood pressure (mmHg)')
    blood_pressure_diastolic = fields.Integer(string='BP Diastolic',
                                            help='Diastolic blood pressure (mmHg)')
    blood_pressure_arm = fields.Selection([
        ('left', 'Left Arm'),
        ('right', 'Right Arm'),
    ], string='Blood Pressure Arm',
       help='Arm used for blood pressure measurement')
    blood_pressure_position = fields.Selection([
        ('sitting', 'Sitting'),
        ('lying', 'Lying Down'),
        ('standing', 'Standing'),
    ], string='Patient Position',
       help='Patient position during measurement')

    # Heart Rate
    heart_rate = fields.Integer(string='Heart Rate (bpm)',
                               help='Heart rate in beats per minute')
    heart_rate_rhythm = fields.Selection([
        ('regular', 'Regular'),
        ('irregular', 'Irregular'),
    ], string='Heart Rhythm',
       help='Heart rhythm regularity')

    # Respiratory
    respiratory_rate = fields.Integer(string='Respiratory Rate (/min)',
                                     help='Respirations per minute')

    # Oxygen Saturation
    oxygen_saturation = fields.Integer(string='O2 Saturation (%)',
                                      help='Blood oxygen saturation percentage')

    # Physical Measurements
    weight = fields.Float(string='Weight (kg)',
                         digits=(5, 2),
                         help='Weight in kilograms')
    height = fields.Float(string='Height (cm)',
                         digits=(5, 1),
                         help='Height in centimeters')
    bmi = fields.Float(string='BMI',
                      compute='_compute_bmi',
                      store=True,
                      digits=(5, 1),
                      help='Body Mass Index')

    # Pain Scale
    pain_level = fields.Integer(string='Pain Level (0-10)',
                              help='Patient reported pain level (0-10 scale)')
    pain_location = fields.Text(string='Pain Location',
                               help='Description of pain location')

    # Additional Notes
    notes = fields.Text(string='Notes',
                      help='Additional observations or notes')

    # === Computed Fields ===
    @api.depends('weight', 'height')
    def _compute_bmi(self):
        """Compute Body Mass Index."""
        for record in self:
            if record.weight and record.height:
                # BMI = kg / (m^2)
                height_m = record.height / 100
                record.bmi = record.weight / (height_m ** 2) if height_m > 0 else 0
            else:
                record.bmi = 0

    # === Display Names ===
    def name_get(self):
        """Format display name."""
        result = []
        for record in self:
            name = f"Vitals - {record.patient_id.name}"
            if record.date_taken:
                name += f" ({record.date_taken.strftime('%Y-%m-%d %H:%M')})"
            result.append((record.id, name))
        return result

    # === Constraints ===
    @api.constrains('pain_level')
    def _check_pain_level(self):
        """Validate pain level range."""
        for record in self:
            if record.pain_level is not None and (record.pain_level < 0 or record.pain_level > 10):
                raise models.ValidationError(
                    'Pain level must be between 0 and 10'
                )

    @api.constrains('oxygen_saturation')
    def _check_oxygen_saturation(self):
        """Validate oxygen saturation range."""
        for record in self:
            if record.oxygen_saturation is not None and (record.oxygen_saturation < 0 or record.oxygen_saturation > 100):
                raise models.ValidationError(
                    'Oxygen saturation must be between 0 and 100%'
                )
