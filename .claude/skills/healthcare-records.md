# Healthcare Records Skill

## Description
Record and manage patient medical records including vitals, visit notes, diagnoses, and prescriptions.

## Triggers
- Patient visit completed
- Vitals recording needed
- Medical history update required

## MCP Tools Used
- `odoo_mcp.get_patient` - Get patient profile
- `odoo_mcp.update_patient_vitals` - Record visit vitals
- `odoo_mcp.update_appointment_status` - Mark appointment completed
- `vault_reader` - Read patient notes from vault
- `task_writer` - Create follow-up tasks if needed

## Task Format
```yaml
---
title: "Record Visit - {Patient Name}"
created: 2026-02-13
priority: normal
status: inbox
type: healthcare_records
assignee: claude

## Description
Record medical information from **{Patient Name}** visit on {visit_date}.

## Visit Details
- **Appointment ID:** {appointment_id}
- **Patient:** {patient_name}
- **Patient ID:** {patient_id}
- **Doctor:** {doctor_name}
- **Date:** {visit_date}
- **Visit Type:** {visit_type}

## Vitals to Record
- Temperature: {temperature}°C
- Blood Pressure: {bp_systolic}/{bp_diastolic} mmHg
- Heart Rate: {heart_rate} bpm
- Weight: {weight} kg
- Height: {height} cm

## Visit Notes
{visit_notes}

## Diagnosis
{diagnosis}

## Prescription
{prescription}

## Steps
1. [ ] Record patient vitals in Odoo
2. [ ] Update appointment with visit details
3. [ ] Mark appointment as completed
4. [ ] Create follow-up task if needed
5. [ ] Move this task to Done/
```

## Execution Flow

### 1. Parse Task
Extract from task file:
- `patient_id` - Patient record ID
- `appointment_id` - Appointment ID
- Vitals data (temperature, BP, heart rate, weight, height)
- `visit_notes` - Visit notes
- `diagnosis` - Diagnosis from visit
- `prescription` - Prescribed medications

### 2. Record Vitals
```python
# Use MCP tool
await mcp.odoo_mcp.update_patient_vitals(
    patient_id=patient_id,
    temperature=temperature,
    blood_pressure_systolic=bp_systolic,
    blood_pressure_diastolic=bp_diastolic,
    heart_rate=heart_rate,
    weight=weight,
    height=height,
    notes=f"Visit on {visit_date}: {visit_notes}"
)
```

### 3. Update Appointment
```python
# Update appointment with visit details
await mcp.odoo_mcp.update_appointment_status(
    appointment_id=appointment_id,
    status="completed"
)

# Additional notes could be added to the appointment
# via direct Odoo model write if needed
```

### 4. Check for Follow-up Needs
Create follow-up task if:
- High-risk patient
- Abnormal vitals detected
- New diagnosis requiring monitoring
- Prescription needs review

```python
if needs_followup:
    vault.create_task(
        title=f"Follow-up - {patient_name}",
        description=f"Review patient {patient_name} after {visit_type} visit",
        priority="normal" if risk_category == "low" else "high",
        folder="Needs_Action/"
    )
```

### 5. Complete Task
```python
# Move to Done/
vault.move_task(
    task_id=task_id,
    target_folder="Done/"
)
# Update dashboard
vault.update_dashboard(
    section="Healthcare",
    update=f"Recorded visit for {patient_name} - Vitals: {temperature}°C, BP: {bp_systolic}/{bp_diastolic}"
)
```

## Vital Signs Analysis

### Normal Ranges
| Vital | Normal Range | Concern |
|-------|-------------|----------|
| Temperature | 36.1-37.2°C | >38°C or <35°C |
| BP Systolic | 90-120 mmHg | >140 or <90 |
| BP Diastolic | 60-80 mmHg | >90 or <60 |
| Heart Rate | 60-100 bpm | >120 or <50 |
| O2 Saturation | 95-100% | <95% |
| BMI | 18.5-25 | >30 or <18.5 |

### Alert Triggers
Create urgent task if:
- Temperature > 38°C or < 35°C
- BP Systolic > 140 or < 90
- O2 Saturation < 95%
- High-risk patient with any abnormal vitals

## Success Criteria
- [ ] All vitals recorded in Odoo
- [ ] Appointment marked as completed
- [ ] Patient last_visit_date updated
- [ ] Follow-up tasks created if needed
- [ ] Task moved to Done/
- [ ] Dashboard.md updated

## Error Handling
| Error | Action |
|-------|--------|
| Patient ID not found | Log error, halt execution |
| Vitals out of range | Flag in notes, create alert task |
| Appointment already completed | Note in task, skip status update |
| Network error to Odoo | Retry 3 times, then log and halt |

## Related Skills
- `healthcare-reminder` - Schedule follow-up appointment
- `healthcare-billing` - Generate invoice for visit
- `vault-reader` - Access patient history
