# -*- coding: utf-8 -*-

from odoo import models, fields, api


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

    # === Visit Details ===
    notes = fields.Text(string='Notes',
                      help='Additional notes about the appointment')
    chief_complaint = fields.Text(string='Chief Complaint',
                                  help="Patient's primary reason for visit")
    diagnosis = fields.Text(string='Diagnosis',
                           help='Diagnosis from the visit')
    prescription = fields.Text(string='Prescription',
                              help='Prescribed medications and treatments')
    vitals_recorded = fields.Boolean(string='Vitals Recorded',
                                      default=False,
                                      help='Whether patient vitals were recorded')

    # === Computed Fields ===
    @api.depends('patient_id', 'doctor_id', 'appointment_type')
    def _compute_name(self):
        """Compute appointment name."""
        for apt in self:
            patient_name = apt.patient_id.name if apt.patient_id else 'Patient'
            doctor_name = apt.doctor_id.name if apt.doctor_id else 'Doctor'
            apt_type = dict(apt._fields['appointment_type'].get_values(
                apt.appointment_type)).get(apt.appointment_type, 'Appointment')
            apt.name = f"{apt_type} - {patient_name} with {doctor_name}"

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
            apt.patient_id.write({
                'last_visit_date': fields.Date.today(),
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
