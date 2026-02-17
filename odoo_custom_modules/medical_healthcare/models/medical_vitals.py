# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MedicalVitals(models.Model):
    _name = 'medical.vitals'
    _description = 'Medical Vitals'
    _order = 'date_taken desc'

    # === Relationships ===
    patient_id = fields.Many2one('res.partner', string='Patient',
                                required=True, ondelete='cascade',
                                domain=[('is_patient', '=', True)])
    appointment_id = fields.Many2one('medical.appointment', string='Appointment',
                                      ondelete='cascade')

    # === Vitals ===
    date_taken = fields.Datetime(string='Date Taken', required=True,
                                      default=fields.Datetime.now,
                                      help='When vitals were recorded')

    # Basic Vitals
    temperature = fields.Float(string='Temperature (°C)',
                                  help='Body temperature in Celsius')
    blood_pressure_systolic = fields.Integer(string='BP Systolic (mmHg)',
                                          help='Systolic blood pressure')
    blood_pressure_diastolic = fields.Integer(string='BP Diastolic (mmHg)',
                                           help='Diastolic blood pressure')
    heart_rate = fields.Integer(string='Heart Rate (bpm)',
                                     help='Heart rate in beats per minute')
    respiratory_rate = fields.Integer(string='Respiratory Rate (/min)',
                                             help='Respirations per minute')
    oxygen_saturation = fields.Integer(string='O2 Saturation (%)',
                                              help='Oxygen saturation percentage')

    # Body Measurements
    weight = fields.Float(string='Weight (kg)')
    height = fields.Float(string='Height (cm)')

    # Computed
    bmi = fields.Float(string='BMI',
                           compute='_compute_bmi',
                           store=True,
                           help='Body Mass Index')

    # Additional Vitals
    blood_glucose = fields.Float(string='Blood Glucose (mg/dL)',
                                  help='Blood glucose level')
    pain_level = fields.Integer(string='Pain Level (0-10)',
                                help='Patient reported pain level')

    # Additional Info
    recorded_by = fields.Many2one('res.users', string='Recorded By',
                                   default=lambda self: self.env.user,
                                   help='User who recorded the vitals')
    abnormal_flags = fields.Text(string='Abnormal Flags',
                                 compute='_compute_abnormal_flags',
                                 store=True,
                                 help='Auto-detected abnormal values')
    notes = fields.Text(string='Notes')

    @api.depends('weight', 'height')
    def _compute_bmi(self):
        """Compute BMI from weight and height"""
        for record in self:
            if record.weight and record.height:
                # BMI = weight(kg) / height(m)^2
                height_m = record.height / 100  # cm to m
                record.bmi = record.weight / (height_m ** 2)

    @api.depends('temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
                 'heart_rate', 'respiratory_rate', 'oxygen_saturation', 'blood_glucose', 'pain_level')
    def _compute_abnormal_flags(self):
        """Compute abnormal vitals flags"""
        for record in self:
            flags = []

            # Temperature: Normal range 36.1-37.2°C
            if record.temperature:
                if record.temperature < 35.0:
                    flags.append('LOW_TEMPERATURE')
                elif record.temperature > 38.0:
                    flags.append('HIGH_TEMPERATURE')

            # Blood Pressure: Systolic >140 or <90, Diastolic >90 or <60
            if record.blood_pressure_systolic:
                if record.blood_pressure_systolic > 140:
                    flags.append('HIGH_SYSTOLIC_BP')
                elif record.blood_pressure_systolic < 90:
                    flags.append('LOW_SYSTOLIC_BP')

            if record.blood_pressure_diastolic:
                if record.blood_pressure_diastolic > 90:
                    flags.append('HIGH_DIASTOLIC_BP')
                elif record.blood_pressure_diastolic < 60:
                    flags.append('LOW_DIASTOLIC_BP')

            # Heart Rate: Normal 60-100 bpm
            if record.heart_rate:
                if record.heart_rate < 60:
                    flags.append('LOW_HEART_RATE')
                elif record.heart_rate > 100:
                    flags.append('HIGH_HEART_RATE')

            # Respiratory Rate: Normal 12-20 /min
            if record.respiratory_rate:
                if record.respiratory_rate < 12:
                    flags.append('LOW_RESPIRATORY_RATE')
                elif record.respiratory_rate > 20:
                    flags.append('HIGH_RESPIRATORY_RATE')

            # Oxygen Saturation: Normal 95-100%
            if record.oxygen_saturation:
                if record.oxygen_saturation < 95:
                    flags.append('LOW_OXYGEN_SATURATION')

            # Blood Glucose: Fasting >126, Random >200
            if record.blood_glucose:
                if record.blood_glucose > 200:
                    flags.append('HIGH_BLOOD_GLUCOSE')
                elif record.blood_glucose < 70:
                    flags.append('LOW_BLOOD_GLUCOSE')

            # Pain Level: >7 requires attention
            if record.pain_level and record.pain_level > 7:
                flags.append('HIGH_PAIN_LEVEL')

            record.abnormal_flags = ', '.join(flags) if flags else ''
