# Healthcare Reminder Skill

## Description
Automatically send appointment reminders to patients via WhatsApp or Email based on their preferred contact method.

## Triggers
- Appointment reminder tasks created in `Needs_Action/` folder by `appointment_reminder_watcher`

## MCP Tools Used
- `odoo_mcp.get_patient` - Get patient contact information
- `odoo_mcp.get_upcoming_appointments` - Verify appointment details
- `whatsapp_mcp.send_message` - Send WhatsApp reminder
- `gmail_mcp.send_email` - Send email reminder
- `odoo_mcp.mark_appointment_reminder_sent` - Mark reminder as sent

## Task Format
```yaml
---
title: "Send Appointment Reminder - {Patient Name}"
created: 2026-02-13
priority: high
status: inbox
type: healthcare_reminder
assignee: claude
tags: [healthcare, appointment, reminder, high]

## Description
Send appointment reminder to **{Patient Name}** for appointment with **Dr. {Doctor Name}**.

## Appointment Details
- **Appointment ID:** {appointment_id}
- **Patient:** {patient_name}
- **Doctor:** Dr. {doctor_name}
- **Date/Time:** {appointment_datetime}
- **Urgency:** {urgency}

## Action Required
Send reminder via **{contact_method}**.

**Contact Info:**
- Phone: {patient_phone}
- Email: {patient_email}

## Reminder Message Template
```
Dear {patient_name},

This is a reminder of your appointment with Dr. {doctor_name} on {appointment_date} at {appointment_time}.

Please arrive 15 minutes early.

If you need to reschedule, please reply to this message or call our clinic.

Best regards,
{Clinic Name}
```

## Steps
1. [ ] Get patient contact info from appointment
2. [ ] Send reminder via {contact_method}
3. [ ] Mark appointment reminder as sent in Odoo
4. [ ] Move this task to Done/
5. [ ] Update Dashboard.md with reminder sent

## Notes
- If patient responds with reschedule request, create new task to update appointment
- If patient cancels, mark appointment as 'cancelled'
- Track response for follow-up if needed
```

## Execution Flow

### 1. Parse Task
Extract from task file:
- `appointment_id` - Appointment record ID
- `patient_name` - Patient name
- `patient_phone` - Patient phone number
- `patient_email` - Patient email address
- `contact_method` - 'whatsapp' or 'email'
- `urgency` - 'urgent', 'high', 'normal'

### 2. Verify Appointment
```python
# Use MCP tool
result = await mcp.odoo_mcp.get_upcoming_appointments(days=2)
# Verify appointment exists and is still scheduled
```

### 3. Send Reminder

#### WhatsApp Method
```python
# Use MCP tool
await mcp.whatsapp_mcp.send_message(
    phone=patient_phone,
    message=f"""Dear {patient_name},

This is a reminder of your appointment on {appointment_date} at {appointment_time}.

Please arrive 15 minutes early.

Reply CONFIRM or call to reschedule."""
)
```

#### Email Method
```python
# Use MCP tool
await mcp.gmail_mcp.send_email(
    to=patient_email,
    subject=f"Appointment Reminder - {appointment_date}",
    body=f"""Dear {patient_name},

This is a reminder of your appointment on {appointment_date} at {appointment_time}.

Please arrive 15 minutes early.

If you need to reschedule, please reply to this email or call our clinic.

Best regards"""
)
```

### 4. Mark as Sent
```python
# Use MCP tool
await mcp.odoo_mcp.mark_appointment_reminder_sent(
    appointment_id=appointment_id,
    method=contact_method
)
```

### 5. Complete Task
```python
# Move task to Done/
vault.move_task(
    task_id=task_id,
    target_folder="Done/"
)
# Update dashboard
vault.update_dashboard(
    section="Healthcare",
    update=f"Sent appointment reminder to {patient_name} via {contact_method}"
)
```

## Success Criteria
- [ ] Reminder sent successfully via preferred method
- [ ] Appointment marked with reminder_sent=True
- [ ] Task moved to Done/
- [ ] Dashboard.md updated

## Error Handling
| Error | Action |
|-------|--------|
| Patient phone invalid | Try email method instead |
| WhatsApp not connected | Fall back to email |
| Email send failed | Log error, create follow-up task |
| Appointment cancelled | Skip reminder, note in task |

## Related Skills
- `healthcare-records` - Update patient records
- `healthcare-billing` - Generate invoice after visit
