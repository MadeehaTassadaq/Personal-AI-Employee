"""Appointment Reminder Watcher.

Monitors upcoming healthcare appointments and creates reminder tasks
for the Digital FTE to send via WhatsApp or Email.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.base_watcher import BaseWatcher
from mcp_services.odoo_mcp.jsonrpc_client import get_client


class AppointmentReminderWatcher(BaseWatcher):
    """Monitors upcoming appointments and creates reminder tasks."""

    name = "appointment_reminder_watcher"
    description = "Monitors upcoming appointments and creates reminder tasks"

    def __init__(self):
        super().__init__()
        self.odoo_url = os.getenv("ODOO_URL")
        self.odoo_db = os.getenv("ODOO_DB")
        self.odoo_username = os.getenv("ODOO_USERNAME")
        self.odoo_password = os.getenv("ODOO_PASSWORD")

        # How many days ahead to check for appointments
        self.reminder_days = int(os.getenv("APPOINTMENT_REMINDER_DAYS", "2"))

        # Vault path for creating tasks
        self.vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))

    def is_enabled(self) -> bool:
        """Check if Odoo is configured."""
        return all([
            self.odoo_url,
            self.odoo_db,
            self.odoo_username,
            self.odoo_password
        ])

    async def check_for_updates(self):
        """Check for upcoming appointments that need reminders."""
        if not self.is_enabled():
            return []

        updates = []

        try:
            client = get_client(
                url=self.odoo_url,
                db=self.odoo_db,
                username=self.odoo_username,
                password=self.odoo_password
            )
            await client.authenticate()

            # Get appointments in the reminder window
            from_date = datetime.now().isoformat()
            to_date = (datetime.now() + timedelta(days=self.reminder_days)).isoformat()

            appointments = await client.search_read(
                "medical.appointment",
                [
                    ("status", "in", ["scheduled", "confirmed"]),
                    ("appointment_date", ">=", from_date),
                    ("appointment_date", "<=", to_date),
                    ("reminder_sent", "=", False)
                ],
                ["id", "name", "patient_id", "doctor_id", "appointment_date", "appointment_type"],
                limit=50,
                order="appointment_date asc"
            )

            # Create reminder tasks for each appointment
            for apt in appointments:
                task = await self._create_reminder_task(client, apt)
                if task:
                    updates.append(task)

            return updates

        except Exception as e:
            self.logger.error(f"Error checking appointments: {e}")
            return []

    async def _create_reminder_task(self, client, appointment):
        """Create a reminder task in the vault."""
        try:
            # Get full details
            apt_id = appointment["id"]
            full_details = await client.read("medical.appointment", [apt_id],
                                         ["patient_id", "doctor_id", "appointment_date", "patient_phone", "patient_email"])

            if not full_details:
                return None

            apt = full_details[0]

            # Extract patient and doctor info
            patient = apt.get("patient_id", [0, ""])
            patient_name = patient[1] if isinstance(patient, list) and len(patient) > 1 else "Unknown"
            patient_id = patient[0] if isinstance(patient, list) else apt.get("patient_id")

            doctor = apt.get("doctor_id", [0, ""])
            doctor_name = doctor[1] if isinstance(doctor, list) and len(doctor) > 1 else "Unknown"

            appointment_date = apt.get("appointment_date", "")
            patient_phone = apt.get("patient_phone", "")
            patient_email = apt.get("patient_email", "")

            # Determine urgency
            apt_datetime = datetime.fromisoformat(appointment_date) if appointment_date else datetime.now()
            hours_until = (apt_datetime - datetime.now()).total_seconds() / 3600

            if hours_until < 24:
                urgency = "urgent"
                priority = "urgent"
            elif hours_until < 48:
                urgency = "soon"
                priority = "high"
            else:
                urgency = "upcoming"
                priority = "normal"

            # Determine contact method
            contact_method = "whatsapp" if patient_phone else "email"

            # Create task file
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            task_filename = f"{timestamp}-appointment-reminder-{patient_name.replace(' ', '-').lower()}.md"

            task_content = self._generate_task_content(
                apt_id, patient_name, doctor_name, appointment_date,
                urgency, contact_method, patient_phone, patient_email
            )

            # Write to Needs_Action folder
            needs_action_path = self.vault_path / "Needs_Action"
            needs_action_path.mkdir(parents=True, exist_ok=True)

            task_path = needs_action_path / task_filename
            task_path.write_text(task_content)

            self.logger.info(f"Created reminder task for appointment {apt_id}: {patient_name} with {doctor_name}")

            return {
                "type": "appointment_reminder",
                "appointment_id": apt_id,
                "patient": patient_name,
                "doctor": doctor_name,
                "datetime": appointment_date,
                "urgency": urgency,
                "task_file": str(task_path)
            }

        except Exception as e:
            self.logger.error(f"Error creating reminder task: {e}")
            return None

    def _generate_task_content(self, appointment_id, patient_name, doctor_name,
                             appointment_date, urgency, contact_method,
                             patient_phone, patient_email):
        """Generate the task file content."""
        return f"""---
title: "Send Appointment Reminder - {patient_name}"
created: {datetime.now().strftime('%Y-%m-%d')}
priority: {urgency}
status: inbox
type: healthcare_reminder
assignee: claude
tags: [healthcare, appointment, reminder, {urgency}]

## Description
Send appointment reminder to **{patient_name}** for appointment with **Dr. {doctor_name}**.

## Appointment Details
- **Appointment ID:** {appointment_id}
- **Patient:** {patient_name}
- **Doctor:** Dr. {doctor_name}
- **Date/Time:** {appointment_date}
- **Urgency:** {urgency}

## Action Required
Send reminder via **{contact_method.upper()}**.

**Contact Info:**
- Phone: {patient_phone or 'N/A'}
- Email: {patient_email or 'N/A'}

## Reminder Message
```
Dear {patient_name}, this is a reminder of your appointment with Dr. {doctor_name} on {appointment_date}.

Please arrive 15 minutes early.

Reply CONFIRM or call the clinic to reschedule.
```

## Steps
1. [ ] Get patient contact info from appointment
2. [ ] Send reminder via {contact_method.upper()}
3. [ ] Mark appointment reminder as sent in Odoo: Use `mark_appointment_reminder_sent(appointment_id={appointment_id}, method="{contact_method}")`
4. [ ] Move this task to Done/ after sending
5. [ ] Update Dashboard.md with reminder sent

## Notes
- If patient responds with reschedule request, update appointment in Odoo
- If patient cancels, mark appointment as 'cancelled'
- Track response for follow-up if needed
"""

    async def on_new_item(self, item):
        """Handle new appointment - not typically used for reminders."""
        # Reminders are generated from check_for_updates
        pass


# Health Check Watcher for High-Risk Patients
class HighRiskPatientWatcher(BaseWatcher):
    """Monitors high-risk patients and creates follow-up tasks."""

    name = "high_risk_patient_watcher"
    description = "Monitors high-risk patients for follow-up needs"

    def __init__(self):
        super().__init__()
        self.vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))

    def is_enabled(self) -> bool:
        """Check if Odoo is configured."""
        return all([
            os.getenv("ODOO_URL"),
            os.getenv("ODOO_DB"),
            os.getenv("ODOO_USERNAME"),
            os.getenv("ODOO_PASSWORD")
        ])

    async def check_for_updates(self):
        """Check for high-risk patients needing follow-up."""
        if not self.is_enabled():
            return []

        updates = []

        try:
            client = get_client()
            await client.authenticate()

            # Get high-risk patients with recent visits
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()

            patients = await client.search_read(
                "res.partner",
                [
                    ("is_patient", "=", True),
                    ("risk_category", "=", "high"),
                    "|",
                    ("pregnancy_status", "=", "pregnant"),
                    ("pregnancy_status", "=", "high_risk")
                ],
                ["id", "name", "medical_record_number", "risk_category", "pregnancy_status",
                 "last_visit_date", "phone", "email"],
                limit=20
            )

            # Create follow-up tasks for high-risk patients
            for patient in patients:
                last_visit = patient.get("last_visit_date")
                needs_followup = not last_visit or last_visit < cutoff_date

                if needs_followup:
                    task = await self._create_followup_task(client, patient)
                    if task:
                        updates.append(task)

            return updates

        except Exception as e:
            self.logger.error(f"Error checking high-risk patients: {e}")
            return []

    async def _create_followup_task(self, client, patient):
        """Create a follow-up task for high-risk patient."""
        try:
            patient_id = patient["id"]
            patient_name = patient["name"]
            risk_category = patient.get("risk_category", "unknown")
            pregnancy_status = patient.get("pregnancy_status", "not_applicable")

            # Determine reason
            if pregnancy_status in ["pregnant", "high_risk"]:
                reason = "High-risk pregnancy"
                priority = "high"
            elif risk_category == "high":
                reason = "High-risk category"
                priority = "normal"
            else:
                reason = "Risk monitoring"
                priority = "low"

            # Create task
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            task_filename = f"{timestamp}-followup-{patient_name.replace(' ', '-').lower()}.md"

            task_content = f"""---
title: "Follow-up - {patient_name} ({reason})"
created: {datetime.now().strftime('%Y-%m-%d')}
priority: {priority}
status: inbox
type: healthcare_followup
assignee: claude

## Description
Follow-up with high-risk patient **{patient_name}**.

## Patient Details
- **Name:** {patient_name}
- **Patient ID:** {patient_id}
- **MR#:** {patient.get('medical_record_number', 'N/A')}
- **Risk Category:** {risk_category}
- **Pregnancy Status:** {pregnancy_status}
- **Reason:** {reason}

## Action Required
1. [ ] Check if patient has upcoming appointments scheduled
2. [ ] If no recent appointment, consider reaching out
3. [ ] Update task with findings

## Notes
- High-risk patients need regular monitoring
- Pregnancy patients require prenatal checkup tracking
"""

            needs_action_path = self.vault_path / "Needs_Action"
            needs_action_path.mkdir(parents=True, exist_ok=True)

            task_path = needs_action_path / task_filename
            task_path.write_text(task_content)

            self.logger.info(f"Created follow-up task for high-risk patient: {patient_name}")

            return {
                "type": "high_risk_followup",
                "patient_id": patient_id,
                "patient": patient_name,
                "reason": reason,
                "task_file": str(task_path)
            }

        except Exception as e:
            self.logger.error(f"Error creating follow-up task: {e}")
            return None


# Create instances for the watcher system
watcher_classes = [AppointmentReminderWatcher, HighRiskPatientWatcher]
