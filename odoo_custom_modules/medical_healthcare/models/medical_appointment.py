# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta


class MedicalAppointment(models.Model):
    _name = 'medical.appointment'
    _description = 'Medical Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date asc'

    # === Relationships ===
    patient_id = fields.Many2one('res.partner', string='Patient',
                                required=True, ondelete='cascade',
                                domain=[('is_patient', '=', True)],
                                tracking=True)
    doctor_id = fields.Many2one('res.partner', string='Doctor/Physician',
                                required=True, ondelete='restrict',
                                domain=[('is_doctor', '=', True)],
                                tracking=True)

    # === Appointment Details ===
    name = fields.Char(string='Description', required=True,
                      compute='_compute_name', store=True,
                      help='Appointment description')
    appointment_date = fields.Datetime(string='Date & Time',
                                      required=True,
                                      tracking=True,
                                      help='Scheduled appointment date and time')
    duration = fields.Float(string='Duration (minutes)',
                          default=30,
                          help='Appointment duration in minutes')
    appointment_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('followup', 'Follow-up'),
        ('checkup', 'Regular Check-up'),
        ('emergency', 'Emergency'),
        ('prenatal', 'Prenatal Checkup'),
        ('lab_test', 'Lab Test'),
        ('vaccination', 'Vaccination'),
        ('procedure', 'Medical Procedure'),
    ], string='Type', required=True, default='consultation',
       help='Type of appointment')

    # === Status ===
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], string='Status', default='scheduled', tracking=True,
       help='Current appointment status')

    # === AI Triage Classification ===
    urgency = fields.Selection([
        ('emergency', 'Emergency'),
        ('urgent', 'Urgent'),
        ('routine', 'Routine'),
    ], string='Urgency', default='routine',
       help='AI-triaged urgency level')
    urgency_confidence = fields.Float(string='Urgency Confidence',
                                    help='AI confidence score for urgency classification (0.0-1.0)')
    triage_correlation_id = fields.Char(string='Triage Correlation ID',
                                      help='Correlation ID for AI triage audit trail')

    # === Patient Reported Information ===
    symptoms = fields.Text(string='Reported Symptoms',
                          help='Symptoms reported by patient during intake')
    patient_message_excerpt = fields.Text(string='Original Message',
                                       help='Excerpt from patient message that triggered appointment')

    # === Location ===
    location = fields.Char(string='Location',
                         help='Physical location for appointment (clinic, hospital, etc.)')

    # === Reminder ===
    reminder_sent = fields.Boolean(string='Reminder Sent',
                                  default=False,
                                  help='Whether appointment reminder has been sent')
    reminder_sent_date = fields.Datetime(string='Reminder Sent Date',
                                        help='When reminder was sent')
    reminder_method = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('phone', 'Phone Call'),
    ], string='Reminder Method',
       help='Method used to send reminder')

    # === Automated Reminders ===
    reminder_config_ids = fields.Many2many(
        'medical.reminder.config',
        'medical_appointment_reminder_config_rel',
        'appointment_id',
        'config_id',
        string='Reminder Configurations',
        help='Which reminder configurations to apply'
    )

    reminder_history_ids = fields.One2many(
        'medical.reminder.history',
        'appointment_id',
        string='Reminder History'
    )

    reminder_count = fields.Integer(
        string='Reminders Sent',
        compute='_compute_reminder_count',
        store=False
    )

    disable_reminders = fields.Boolean(
        string='Disable Reminders',
        default=False,
        help='Check to disable automatic reminders for this appointment'
    )

    patient_confirmed = fields.Boolean(
        string='Patient Confirmed',
        default=False,
        help='Patient confirmed attendance via WhatsApp response'
    )

    # === Visit Details ===
    notes = fields.Text(string='Notes',
                      help='Additional notes about appointment')
    chief_complaint = fields.Text(string='Chief Complaint',
                                  help="Patient's primary reason for visit")
    diagnosis = fields.Text(string='Diagnosis',
                           help='Diagnosis from visit')
    prescription = fields.Text(string='Prescription',
                              help='Prescribed medications and treatments')
    vitals_recorded = fields.Boolean(string='Vitals Recorded',
                                      default=False,
                                      help='Whether patient vitals were recorded')

    # === Computed Fields ===
    @api.depends('patient_id', 'doctor_id', 'appointment_type')
    def _compute_name(self):
        """Compute appointment name."""
        # Type labels mapping
        type_labels = {
            'consultation': 'Consultation',
            'followup': 'Follow-up',
            'checkup': 'Regular Check-up',
            'emergency': 'Emergency',
            'prenatal': 'Prenatal Checkup',
            'lab_test': 'Lab Test',
            'vaccination': 'Vaccination',
            'procedure': 'Medical Procedure',
        }
        for apt in self:
            patient_name = apt.patient_id.name if apt.patient_id else 'Patient'
            doctor_name = apt.doctor_id.name if apt.doctor_id else 'Doctor'
            apt_type = type_labels.get(apt.appointment_type, 'Appointment')
            apt.name = f"{apt_type} - {patient_name} with {doctor_name}"

    @api.depends('reminder_history_ids')
    def _compute_reminder_count(self):
        """Compute number of reminders sent"""
        for apt in self:
            apt.reminder_count = len(apt.reminder_history_ids.filtered(lambda r: r.status == 'sent'))

    # === Actions ===
    def action_confirm(self):
        """Mark appointment as confirmed."""
        self.write({'status': 'confirmed'})
        return True

    def action_in_progress(self):
        """Mark appointment as in progress."""
        self.write({'status': 'in_progress'})
        return True

    def action_complete(self):
        """Mark appointment as completed and update patient visit."""
        for apt in self:
            if apt.patient_id:
                apt.patient_id.write({
                    'last_visit_date': fields.Date.today()
                })
        apt.write({'status': 'completed'})
        return True

    def action_cancel(self):
        """Mark appointment as cancelled."""
        self.write({'status': 'cancelled'})
        return True

    def action_no_show(self):
        """Mark appointment as no show."""
        self.write({'status': 'no_show'})
        return True

    def action_send_manual_reminder(self):
        """Send manual reminder now"""
        for apt in self:
            # Create a one-time reminder config
            config = self.env['medical.reminder.config'].create({
                'name': f'Manual Reminder - {apt.name}',
                'reminder_hours_before': 0,
                'send_whatsapp': True,
                'whatsapp_template': 'Dear {patient_name}, reminder: appointment on {appointment_date} at {appointment_time}. Please reply YES to confirm.'
            })

            result = config.send_reminder(apt)

            # Create history
            self.env['medical.reminder.history'].create_reminder_record(
                appointment=apt,
                config=config,
                status='sent' if result.get('success') else 'failed',
                message=result.get('message', ''),
                error=result.get('message', '') if not result.get('success') else ''
            )

            apt.write({
                'reminder_sent': True,
                'reminder_sent_date': fields.Datetime.now()
            })

        return True

    @api.model
    def create(self, vals):
        """Create appointment with notification."""
        appointment = super(MedicalAppointment, self).create(vals)
        # Send notification if enabled
        appointment.message_post(
            body=f"Appointment scheduled for {appointment.appointment_date}",
            subject=f"New Appointment: {appointment.name}",
            message_type='notification',
        )
        return appointment

    def write(self, vals):
        """Log status changes."""
        result = super(MedicalAppointment, self).write(vals)
        if 'status' in vals:
            for apt in self:
                apt.message_post(
                    body=f"Appointment status changed to: {vals['status']}",
                    subject=f"Status Update: {apt.name}",
                    message_type='notification',
                )
        return result

    @api.model
    def cron_send_reminders(self):
        """Cron job to send automatic reminders"""
        # Get all active reminder configurations
        configs = self.env['medical.reminder.config'].search([
            ('active', '=', True)
        ])

        reminders_sent = 0
        errors = []

        for config in configs:
            try:
                # Find appointments that need reminders
                cutoff = datetime.now() + timedelta(hours=config.reminder_hours_before)
                appointments = self._get_appointments_needing_reminders(config, cutoff)

                for apt in appointments:
                    if apt.disable_reminders:
                        continue

                    # Check if reminder already sent for this config
                    existing = self.env['medical.reminder.history'].search([
                        ('appointment_id', '=', apt.id),
                        ('config_id', '=', config.id)
                    ], limit=1)

                    if existing:
                        continue

                    # Send reminder
                    result = config.send_reminder(apt)

                    # Create history record
                    self.env['medical.reminder.history'].create_reminder_record(
                        appointment=apt,
                        config=config,
                        status='sent' if result.get('success') else 'failed',
                        message=result.get('message', ''),
                        error=result.get('message', '') if not result.get('success') else ''
                    )

                    if result.get('success'):
                        apt.write({
                            'reminder_sent': True,
                            'reminder_sent_date': datetime.now()
                        })
                        reminders_sent += 1
                    else:
                        errors.append(f"Apt {apt.id}: {result.get('message')}")

            except Exception as e:
                errors.append(f"Config {config.id}: {str(e)}")

        return {
            'reminders_sent': reminders_sent,
            'errors': errors
        }

    def _get_appointments_needing_reminders(self, config, cutoff_time):
        """Get appointments that need reminders based on configuration"""
        domain = [
            ('status', 'in', ['scheduled', 'confirmed']),
            ('appointment_date', '>=', fields.Datetime.now()),
            ('appointment_date', '<=', cutoff_time)
        ]

        # Filter by appointment type if specified
        if config.appointment_type_ids:
            apt_types = config.appointment_type_ids.mapped('code')
            domain.append(('appointment_type', 'in', apt_types))

        appointments = self.search(domain)

        # Filter by risk category if needed
        if config.risk_category_filter != 'all':
            filtered = self.browse()
            for apt in appointments:
                if config.risk_category_filter == 'high' and apt.patient_id.risk_category != 'high':
                    continue
                if config.risk_category_filter == 'medium_high' and apt.patient_id.risk_category not in ['medium', 'high']:
                    continue
                filtered |= apt
            appointments = filtered

        return appointments
