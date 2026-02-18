"""Reminder Scheduler Watcher - Sends 24h and 2h appointment reminders automatically.

This watcher runs every 5 minutes to check for upcoming appointments that need reminders.
It sends automated WhatsApp/Email reminders at 24 hours and 2 hours before appointments.

Usage:
    python -m watchers.reminder_scheduler_watcher

Or via PM2:
    pm2 start watchers/reminder_scheduler_watcher.py --interpreter python3 --name reminder-scheduler
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.base_watcher import BaseWatcher


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ReminderSchedulerWatcher(BaseWatcher):
    """Watcher for sending automated appointment reminders.

    Features:
    - Runs every 5 minutes (configurable)
    - Checks for appointments in next 48 hours
    - Sends 24h and 2h reminders automatically
    - Tracks sent reminders to prevent duplicates
    - Logs all actions to audit trail
    """

    # Reminder intervals in hours before appointment
    REMINDER_INTERVALS = [24, 2]

    # Time window in minutes for sending reminders
    TIME_WINDOW = 5

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 300,
        api_base_url: str = None
    ):
        """Initialize the reminder scheduler watcher.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Seconds between checks (default: 300 = 5 minutes)
            api_base_url: Base URL for healthcare API
        """
        super().__init__(vault_path, check_interval)

        # Configuration
        self.api_base_url = api_base_url or os.getenv(
            "API_BASE_URL",
            "http://localhost:8000"
        )
        self.enabled = os.getenv("AUTO_REMINDERS_ENABLED", "true").lower() == "true"
        self.reminder_24h_enabled = os.getenv("REMINDER_HOURS_24", "true").lower() == "true"
        self.reminder_2h_enabled = os.getenv("REMINDER_HOURS_2", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # Build enabled intervals
        self.enabled_intervals = []
        if self.reminder_24h_enabled:
            self.enabled_intervals.append(24)
        if self.reminder_2h_enabled:
            self.enabled_intervals.append(2)

        # Rate limiting
        self.last_send_time = 0
        self.min_send_interval = 1.0  # 1 second between sends

        logger.info(
            f"ReminderSchedulerWatcher initialized "
            f"(interval={check_interval}s, enabled_intervals={self.enabled_intervals})"
        )

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check for appointments that need reminders.

        Returns:
            List of appointment dicts that need reminders
        """
        if not self.enabled or not self.enabled_intervals:
            return []

        try:
            results = []

            # Check each reminder interval
            for hours_before in self.enabled_intervals:
                # Get appointments due for reminder
                response = httpx.get(
                    f"{self.api_base_url}/api/healthcare/appointments/upcoming/reminder-due",
                    params={"hours": hours_before},
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.warning(f"Failed to get appointments for {hours_before}h reminder: {response.status_code}")
                    continue

                data = response.json()
                appointments = data.get("appointments", [])

                # Check if reminder already sent
                for apt in appointments:
                    apt_id = apt.get("id")
                    if apt_id and not self._reminder_already_sent(apt_id, hours_before):
                        apt["hours_before"] = hours_before
                        results.append(apt)

            if results:
                logger.info(f"Found {len(results)} appointments needing reminders")

            return results

        except Exception as e:
            logger.error(f"Error checking for reminders: {e}")
            return []

    def on_new_item(self, appointment: Dict[str, Any]) -> None:
        """Handle sending a reminder for an appointment.

        Args:
            appointment: Appointment dict with hours_before key
        """
        apt_id = appointment.get("id")
        hours_before = appointment.get("hours_before")
        if not apt_id or hours_before is None:
            return

        try:
            # Extract patient and doctor info
            patient = appointment.get("patient", {})
            doctor = appointment.get("doctor", {})

            # Parse appointment date/time
            apt_date_str = appointment.get("appointment_date", "")
            try:
                apt_datetime = datetime.fromisoformat(apt_date_str.replace("Z", "+00:00"))
            except:
                logger.warning(f"Could not parse appointment date: {apt_date_str}")
                return

            # Determine channel
            phone = patient.get("phone")
            email = patient.get("email")
            channel = "whatsapp" if phone else "email" if email else None

            if not channel:
                logger.warning(f"No contact method for appointment {apt_id}")
                return

            # Generate and send reminder
            if channel == "whatsapp":
                message = self._generate_whatsapp_reminder(
                    patient_name=patient.get("name", "Patient"),
                    appointment_date=apt_datetime.strftime("%Y-%m-%d"),
                    appointment_time=apt_datetime.strftime("%I:%M %p"),
                    doctor_name=doctor.get("name", "Doctor"),
                    hours_before=hours_before
                )
                recipient = phone
            else:
                message = self._generate_email_reminder(
                    patient_name=patient.get("name", "Patient"),
                    appointment_date=apt_datetime.strftime("%Y-%m-%d"),
                    appointment_time=apt_datetime.strftime("%I:%M %p"),
                    doctor_name=doctor.get("name", "Doctor"),
                    hours_before=hours_before
                )
                recipient = email

            # Rate limiting
            elapsed = time.time() - self.last_send_time
            if elapsed < self.min_send_interval:
                time.sleep(self.min_send_interval - elapsed)

            # Send reminder
            if self.dry_run:
                logger.info(
                    f"DRY_RUN: Would send {hours_before}h {channel} reminder "
                    f"to {patient.get('name')} for appointment on {apt_datetime.strftime('%Y-%m-%d %I:%M %p')}"
                )
                success = True
            else:
                success = self._send_reminder_message(
                    appointment_id=apt_id,
                    recipient=recipient,
                    message=message,
                    channel=channel,
                    hours_before=hours_before
                )

            # Track sent reminder
            self._track_reminder_sent(apt_id, hours_before, channel, success)

            self.last_send_time = time.time()

            # Log event
            self.log_event("appointment_reminder_sent", {
                "appointment_id": apt_id,
                "hours_before": hours_before,
                "channel": channel,
                "patient_name": patient.get("name"),
                "success": success,
                "dry_run": self.dry_run
            })

        except Exception as e:
            logger.error(f"Error sending reminder for appointment {apt_id}: {e}")
            self.log_event("appointment_reminder_failed", {
                "appointment_id": apt_id,
                "hours_before": hours_before,
                "error": str(e)
            })

    def _reminder_already_sent(self, appointment_id: int, hours_before: int) -> bool:
        """Check if reminder was already sent.

        Args:
            appointment_id: Appointment ID
            hours_before: Hours before appointment

        Returns:
            True if reminder was already sent
        """
        # Load from tracking file
        tracking_file = self.vault_path / "data" / "sent_reminders.json"
        if not tracking_file.exists():
            return False

        try:
            data = json.loads(tracking_file.read_text())
            for entry in data.get("reminders", []):
                if entry.get("appointment_id") == appointment_id and entry.get("hours_before") == hours_before:
                    # Check if sent in last 48 hours
                    try:
                        sent_at = datetime.fromisoformat(entry.get("sent_at", ""))
                        if (datetime.now() - sent_at).total_seconds() < 48 * 3600:
                            return True
                    except:
                        pass
        except Exception as e:
            logger.warning(f"Error checking reminder status: {e}")

        return False

    def _track_reminder_sent(self, appointment_id: int, hours_before: int, channel: str, success: bool) -> None:
        """Track that a reminder was sent.

        Args:
            appointment_id: Appointment ID
            hours_before: Hours before appointment
            channel: Communication channel
            success: Whether send succeeded
        """
        tracking_file = self.vault_path / "data" / "sent_reminders.json"
        tracking_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Load existing data
            if tracking_file.exists():
                data = json.loads(tracking_file.read_text())
            else:
                data = {"reminders": []}

            # Add new entry
            data["reminders"].append({
                "appointment_id": appointment_id,
                "hours_before": hours_before,
                "channel": channel,
                "success": success,
                "sent_at": datetime.now().isoformat()
            })

            # Keep only last 1000
            data["reminders"] = sorted(
                data["reminders"],
                key=lambda x: x.get("sent_at", ""),
                reverse=True
            )[:1000]

            tracking_file.write_text(json.dumps(data, indent=2))

        except Exception as e:
            logger.error(f"Error tracking reminder: {e}")

    def _send_reminder_message(
        self,
        appointment_id: int,
        recipient: str,
        message: str,
        channel: str,
        hours_before: int
    ) -> bool:
        """Send reminder message via API.

        Args:
            appointment_id: Appointment ID
            recipient: Recipient contact
            message: Message content
            channel: Communication channel
            hours_before: Hours before appointment

        Returns:
            True if send succeeded
        """
        if channel == "whatsapp":
            try:
                response = httpx.post(
                    f"{self.api_base_url}/api/healthcare/whatsapp/send",
                    json={
                        "phone": recipient,
                        "message": message,
                        "appointment_id": appointment_id
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    logger.info(f"WhatsApp {hours_before}h reminder sent for appointment {appointment_id}")
                    return True
                else:
                    logger.warning(f"Failed to send WhatsApp: {response.status_code}")
                    return False

            except Exception as e:
                logger.error(f"Error sending WhatsApp: {e}")
                return False

        elif channel == "email":
            # TODO: Implement email sending
            logger.info(f"Email reminders not yet implemented for appointment {appointment_id}")
            return False

        return False

    def _generate_whatsapp_reminder(
        self,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        doctor_name: str,
        hours_before: int
    ) -> str:
        """Generate WhatsApp reminder message."""
        urgency_emoji = "⏰" if hours_before > 2 else "🔔"

        return f"""{urgency_emoji} *Appointment Reminder*

Dear {patient_name},

This is a reminder about your upcoming appointment:

📅 *Date:* {appointment_date}
⏰ *Time:* {appointment_time}
👨‍⚕️ *Doctor:* {doctor_name}
📍 *Location:* Main Clinic

Your appointment is in {hours_before} hour{'s' if hours_before != 1 else ''}.

Reply CONFIRM to confirm your attendance.
Reply CANCEL if you need to reschedule.

---
This is an automated message.
"""

    def _generate_email_reminder(
        self,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        doctor_name: str,
        hours_before: int
    ) -> str:
        """Generate email reminder message."""
        return f"""Dear {patient_name},

This is a friendly reminder about your upcoming appointment.

APPOINTMENT DETAILS
===================
Date: {appointment_date}
Time: {appointment_time}
Doctor: {doctor_name}
Location: Main Clinic

Your appointment is in {hours_before} hour{'s' if hours_before != 1 else ''}.

CONFIRMATION REQUIRED
=====================
Please confirm your attendance by replying with "CONFIRM".
If you need to reschedule or cancel, please reply with "CANCEL".

---
This is an automated message. Please do not reply to this email address.
"""


def main():
    """Main entry point for running the watcher."""
    vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
    check_interval = int(os.getenv("REMINDER_CHECK_INTERVAL", "300"))  # 5 minutes default
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    watcher = ReminderSchedulerWatcher(
        vault_path=vault_path,
        check_interval=check_interval,
        api_base_url=api_base_url
    )

    try:
        logger.info("Starting Reminder Scheduler Watcher...")
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Stopping Reminder Scheduler Watcher...")
        watcher.stop()


if __name__ == "__main__":
    main()
