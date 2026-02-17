# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests


class ReminderConfig(models.Model):
    _name = 'medical.reminder.config'
    _description = 'Appointment Reminder Configuration'
    _order = 'sequence, id'

    # Basic Fields
    name = fields.Char(string='Reminder Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    # Timing Configuration
    reminder_hours_before = fields.Integer(
        string='Hours Before Appointment',
        required=True,
        default=24,
        help='Send reminder this many hours before appointment'
    )

    # Channel Configuration
    send_whatsapp = fields.Boolean(string='Send via WhatsApp', default=True)
    send_email = fields.Boolean(string='Send via Email', default=False)
    send_sms = fields.Boolean(string='Send via SMS', default=False)

    # Message Templates
    whatsapp_template = fields.Text(
        string='WhatsApp Message Template',
        required=True,
        default='Dear {patient_name}, this is a reminder of your appointment on {appointment_date} at {appointment_time}. Doctor: {doctor_name}. Please reply YES to confirm.',
        help='Available variables: {patient_name}, {appointment_date}, {appointment_time}, {doctor_name}, {clinic_name}'
    )

    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'medical.appointment')]
    )

    sms_template = fields.Text(
        string='SMS Template',
        help='SMS message template (keep under 160 characters)'
    )

    # Filtering
    appointment_type_ids = fields.Many2many(
        'medical.appointment.type',
        'medical_reminder_config_type_rel',
        'config_id',
        'type_id',
        string='Appointment Types',
        help='Leave empty to apply to all appointment types'
    )

    risk_category_filter = fields.Selection([
        ('all', 'All Patients'),
        ('high', 'High Risk Only'),
        ('medium_high', 'Medium & High Risk'),
    ], string='Risk Filter', default='all', required=True)

    # Additional Options
    include_doctor_name = fields.Boolean(string='Include Doctor Name', default=True)
    include_clinic_address = fields.Boolean(string='Include Clinic Address', default=False)
    include_preparation_instructions = fields.Boolean(string='Include Preparation Instructions', default=False)
    preparation_instructions = fields.Text(
        string='Preparation Instructions',
        help='Special instructions for patient (e.g., fasting required)'
    )

    # Statistics
    reminder_sent_count = fields.Integer(string='Reminders Sent', readonly=True)
    last_sent_date = fields.Datetime(string='Last Sent', readonly=True)

    _sql_constraints = [
        ('check_hours_positive', 'CHECK(reminder_hours_before > 0)', 'Hours before must be positive'),
    ]

    @api.constrains('whatsapp_template')
    def _check_whatsapp_template(self):
        for record in self:
            if record.send_whatsapp and not record.whatsapp_template:
                raise ValidationError(_('WhatsApp template is required when WhatsApp is enabled'))

    def get_reminder_message(self, appointment):
        """Generate reminder message for a specific appointment"""
        self.ensure_one()
        # Format appointment date/time
        apt_datetime = fields.Datetime.from_string(appointment.appointment_date)
        appointment_date_str = apt_datetime.strftime('%Y-%m-%d')
        appointment_time_str = apt_datetime.strftime('%I:%M %p')

        # Prepare base message
        message = self.whatsapp_template.format(
            patient_name=appointment.patient_id.name,
            appointment_date=appointment_date_str,
            appointment_time=appointment_time_str,
            doctor_name=appointment.doctor_id.name if appointment.doctor_id else 'Doctor',
            clinic_name=self.env.company.name
        )

        # Add additional information
        if self.include_clinic_address:
            clinic_address = self.env.company.partner_id.contact_address_complete or ''
            if clinic_address:
                message += f"\n\n📍 Location: {clinic_address}"

        if self.include_preparation_instructions and self.preparation_instructions:
            message += f"\n\n📝 Note: {self.preparation_instructions}"

        # Add confirmation request
        message += "\n\nPlease reply YES to confirm or CALL to reschedule."

        return message

    def send_reminder(self, appointment):
        """Send reminder for a specific appointment"""
        self.ensure_one()
        result = {'success': True, 'message': ''}

        if not appointment.patient_id.phone:
            return {
                'success': False,
                'message': f'No phone number for patient {appointment.patient_id.name}'
            }

        message = self.get_reminder_message(appointment)

        # Send via WhatsApp
        if self.send_whatsapp:
            whatsapp_result = self._send_whatsapp(appointment.patient_id.phone, message, appointment)
            result['whatsapp'] = whatsapp_result
            if not whatsapp_result.get('success'):
                result['success'] = False
                result['message'] = whatsapp_result.get('message', 'WhatsApp failed')

        # Send via Email
        if self.send_email and appointment.patient_id.email:
            try:
                if self.email_template_id:
                    self.email_template_id.send_mail(appointment.id, force_send=True)
                    result['email'] = {'success': True, 'message': 'Email sent'}
            except Exception as e:
                result['email'] = {'success': False, 'message': str(e)}

        # Update statistics
        if result['success']:
            self.reminder_sent_count += 1
            self.last_sent_date = fields.Datetime.now()

        return result

    def _send_whatsapp(self, phone, message, appointment):
        """Send WhatsApp message via backend API"""
        try:
            backend_url = self.env['ir.config_parameter'].sudo().get_param('ai_employee.backend_url', 'http://localhost:8000')

            # Format phone number
            phone_clean = phone.replace(' ', '').replace('-', '')

            response = requests.post(
                f'{backend_url}/api/healthcare/whatsapp/send',
                params={
                    'phone': phone_clean,
                    'message': message,
                    'appointment_id': appointment.id
                },
                timeout=30
            )

            if response.status_code == 200:
                return {'success': True, 'message': 'WhatsApp sent successfully'}
            else:
                return {'success': False, 'message': f'HTTP {response.status_code}: {response.text}'}

        except Exception as e:
            return {'success': False, 'message': str(e)}


class MedicalAppointmentType(models.Model):
    _name = 'medical.appointment.type'
    _description = 'Medical Appointment Type'

    name = fields.Char(string='Type Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)

    # Default duration
    default_duration = fields.Integer(string='Default Duration (minutes)', default=30)
