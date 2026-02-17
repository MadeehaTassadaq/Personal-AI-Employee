# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta


class ReminderHistory(models.Model):
    _name = 'medical.reminder.history'
    _description = 'Reminder History'
    _order = 'sent_date desc'

    # Reference
    appointment_id = fields.Many2one(
        'medical.appointment',
        string='Appointment',
        required=True,
        ondelete='cascade'
    )

    patient_id = fields.Many2one(
        related='appointment_id.patient_id',
        string='Patient',
        store=True,
        readonly=True
    )

    doctor_id = fields.Many2one(
        related='appointment_id.doctor_id',
        string='Doctor',
        store=True,
        readonly=True
    )

    # Configuration
    config_id = fields.Many2one(
        'medical.reminder.config',
        string='Reminder Configuration',
        required=True
    )

    # Timing
    sent_date = fields.Datetime(
        string='Sent Date/Time',
        default=fields.Datetime.now,
        required=True
    )

    hours_before = fields.Integer(
        string='Hours Before Appointment',
        readonly=True
    )

    appointment_datetime = fields.Datetime(
        related='appointment_id.appointment_date',
        string='Appointment Date/Time',
        store=True,
        readonly=True
    )

    # Channel & Status
    channel = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('multi', 'Multiple Channels')
    ], string='Channel', required=True, default='whatsapp')

    status = fields.Selection([
        ('sent', 'Sent Successfully'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], string='Status', required=True, default='sent')

    # Message Details
    message = fields.Text(string='Message Sent', readonly=True)

    phone_number = fields.Char(
        related='patient_id.phone',
        string='Phone Number',
        readonly=True
    )

    email_address = fields.Char(
        related='patient_id.email',
        string='Email Address',
        readonly=True
    )

    # Response Tracking
    patient_response = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
        ('no_response', 'No Response Yet')
    ], string='Patient Response', default='no_response')

    response_date = fields.Datetime(string='Response Date')

    # Error Details
    error_message = fields.Text(string='Error Message')

    # Delivery Details
    delivery_status = fields.Selection([
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], string='Delivery Status', default='pending')

    delivery_date = fields.Datetime(string='Delivery Date')

    # Notes
    notes = fields.Text(string='Notes')

    @api.model
    def create_reminder_record(self, appointment, config, status='sent', message='', error=''):
        """Create a reminder history record"""
        sent_date = fields.Datetime.now()
        hours_before = 0
        if appointment.appointment_date:
            apt_datetime = fields.Datetime.from_string(appointment.appointment_date)
            delta = apt_datetime - sent_date
            hours_before = int(delta.total_seconds() / 3600)

        return self.create({
            'appointment_id': appointment.id,
            'config_id': config.id,
            'sent_date': sent_date,
            'hours_before': hours_before,
            'channel': 'multi' if (config.send_whatsapp and config.send_email) else
                     'whatsapp' if config.send_whatsapp else
                     'email' if config.send_email else 'sms',
            'status': status,
            'message': message,
            'error_message': error
        })

    def mark_confirmed(self):
        """Mark reminder as confirmed by patient"""
        self.write({
            'patient_response': 'confirmed',
            'response_date': fields.Datetime.now()
        })

    def mark_no_show(self):
        """Mark reminder as no show"""
        self.write({
            'patient_response': 'no_show',
            'response_date': fields.Datetime.now()
        })
