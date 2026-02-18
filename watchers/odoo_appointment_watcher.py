"""Odoo Appointment Watcher - Monitors Odoo for new appointments and auto-sends confirmations.

This watcher polls Odoo EHR every 60 seconds for new appointments that haven't had
confirmations sent yet. It automatically sends WhatsApp/Email confirmations for new appointments.

Usage:
    python -m watchers.odoo_appointment_watcher

Or via PM2:
    pm2 start watchers/odoo_appointment_watcher.py --interpreter python3 --name odoo-appointment-watcher
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


class OdooAppointmentWatcher(BaseWatcher):
    """Watcher for monitoring Odoo appointments and sending auto-confirmations.

    Features:
    - Polls Odoo every 60 seconds (configurable)
    - Detects new appointments without confirmation_sent flag
    - Sends confirmations via WhatsApp/Email automatically
    - Tracks sent confirmations to prevent duplicates
    - Logs all actions to audit trail
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 60,
        api_base_url: str = None
    ):
        """Initialize the Odoo appointment watcher.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Seconds between Odoo polls (default: 60)
            api_base_url: Base URL for healthcare API (default: http://localhost:8000)
        """
        super().__init__(vault_path, check_interval)

        # Configuration
        self.api_base_url = api_base_url or os.getenv(
            "API_BASE_URL",
            "http://localhost:8000"
        )
        self.enabled = os.getenv("ODOO_APPOINTMENT_WATCHER_ENABLED", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # Tracking
        self.processed_appointments: set[int] = set()
        self._load_processed_appointments()

        logger.info(f"OdooAppointmentWatcher initialized (interval={check_interval}s, enabled={self.enabled})")

    def _load_processed_appointments(self) -> None:
        """Load processed appointment IDs from disk."""
        tracking_file = self.vault_path / "data" / "processed_appointments.json"
        if tracking_file.exists():
            try:
                data = json.loads(tracking_file.read_text())
                self.processed_appointments = set(data.get("appointment_ids", []))
                logger.info(f"Loaded {len(self.processed_appointments)} processed appointment IDs")
            except Exception as e:
                logger.warning(f"Could not load processed appointments: {e}")

    def _save_processed_appointments(self) -> None:
        """Save processed appointment IDs to disk."""
        tracking_file = self.vault_path / "data" / "processed_appointments.json"
        tracking_file.parent.mkdir(parents=True, exist_ok=True)

        # Keep only last 1000
        recent_ids = list(self.processed_appointments)[-1000:]

        data = {"appointment_ids": recent_ids, "updated_at": datetime.now().isoformat()}
        tracking_file.write_text(json.dumps(data, indent=2))

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check Odoo for new appointments that need confirmation.

        Returns:
            List of appointment dicts that need confirmation
        """
        if not self.enabled:
            return []

        try:
            # Get upcoming appointments from healthcare API
            response = httpx.get(
                f"{self.api_base_url}/api/healthcare/appointments/upcoming",
                params={"days": 7},
                timeout=30.0
            )

            if response.status_code != 200:
                logger.error(f"Failed to fetch appointments: {response.status_code}")
                return []

            data = response.json()
            appointments = data.get("appointments", [])

            # Filter for appointments needing confirmation
            new_appointments = []
            for apt in appointments:
                apt_id = apt.get("id")
                if apt_id and apt_id not in self.processed_appointments:
                    # Check if confirmation was already sent
                    if not apt.get("reminder_sent"):  # Using reminder_sent as proxy for confirmation_sent
                        new_appointments.append(apt)

            if new_appointments:
                logger.info(f"Found {len(new_appointments)} new appointments needing confirmation")

            return new_appointments

        except Exception as e:
            logger.error(f"Error checking for appointments: {e}")
            return []

    def on_new_item(self, appointment: Dict[str, Any]) -> None:
        """Handle a new appointment by sending confirmation.

        Args:
            appointment: Appointment dict from Odoo
        """
        apt_id = appointment.get("id")
        if not apt_id:
            return

        try:
            # Extract patient and doctor info
            patient = appointment.get("patient", {})
            if not patient:
                # Fetch patient details if not included
                patient = self._get_patient_details(appointment.get("patient_id"))

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

            # Send confirmation via API
            self._send_confirmation(
                appointment_id=apt_id,
                patient_name=patient.get("name", "Patient"),
                patient_phone=phone,
                patient_email=email,
                appointment_date=apt_datetime.strftime("%Y-%m-%d"),
                appointment_time=apt_datetime.strftime("%I:%M %p"),
                doctor_name=doctor.get("name", "Doctor"),
                channel=channel
            )

            # Mark as processed
            self.processed_appointments.add(apt_id)
            self._save_processed_appointments()

            # Log event
            self.log_event("appointment_confirmation_sent", {
                "appointment_id": apt_id,
                "channel": channel,
                "patient_name": patient.get("name"),
                "dry_run": self.dry_run
            })

        except Exception as e:
            logger.error(f"Error processing appointment {apt_id}: {e}")
            self.log_event("appointment_confirmation_failed", {
                "appointment_id": apt_id,
                "error": str(e)
            })

    def _get_patient_details(self, patient_id: int) -> Dict[str, Any]:
        """Fetch patient details from Odoo.

        Args:
            patient_id: Patient ID

        Returns:
            Patient dict
        """
        try:
            response = httpx.get(
                f"{self.api_base_url}/api/healthcare/patients/{patient_id}",
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()

            return {}

        except Exception as e:
            logger.error(f"Error fetching patient {patient_id}: {e}")
            return {}

    def _send_confirmation(
        self,
        appointment_id: int,
        patient_name: str,
        patient_phone: Optional[str],
        patient_email: Optional[str],
        appointment_date: str,
        appointment_time: str,
        doctor_name: str,
        channel: str
    ) -> None:
        """Send appointment confirmation message.

        Args:
            appointment_id: Appointment ID
            patient_name: Patient name
            patient_phone: Patient phone number
            patient_email: Patient email address
            appointment_date: Appointment date (YYYY-MM-DD)
            appointment_time: Appointment time (HH:MM AM/PM)
            doctor_name: Doctor name
            channel: Communication channel (whatsapp/email)
        """
        if self.dry_run:
            logger.info(
                f"DRY_RUN: Would send {channel} confirmation to {patient_name} "
                f"for appointment on {appointment_date} at {appointment_time}"
            )
            return

        # Generate message
        if channel == "whatsapp":
            message = self._generate_whatsapp_confirmation(
                patient_name, appointment_date, appointment_time, doctor_name
            )
            recipient = patient_phone
        else:
            message = self._generate_email_confirmation(
                patient_name, appointment_date, appointment_time, doctor_name
            )
            recipient = patient_email

        # Send via WhatsApp API endpoint
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
                    logger.info(f"WhatsApp confirmation sent for appointment {appointment_id}")
                else:
                    logger.warning(f"Failed to send WhatsApp: {response.status_code}")

            except Exception as e:
                logger.error(f"Error sending WhatsApp: {e}")

        # TODO: Add email sending support
        elif channel == "email":
            logger.info(f"Email confirmations not yet implemented for appointment {appointment_id}")

    def _generate_whatsapp_confirmation(
        self,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        doctor_name: str
    ) -> str:
        """Generate WhatsApp confirmation message."""
        return f"""🩺 *Appointment Confirmed*

Dear {patient_name},

Your appointment has been scheduled:

📅 *Date:* {appointment_date}
⏰ *Time:* {appointment_time}
👨‍⚕️ *Doctor:* {doctor_name}
📍 *Location:* Main Clinic

Please arrive 10 minutes early.
Reply CONFIRM to confirm or CANCEL to reschedule.

---
This is an automated message.
"""

    def _generate_email_confirmation(
        self,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        doctor_name: str
    ) -> str:
        """Generate email confirmation message."""
        return f"""Dear {patient_name},

Your appointment has been successfully scheduled.

APPOINTMENT DETAILS
===================
Date: {appointment_date}
Time: {appointment_time}
Doctor: {doctor_name}
Location: Main Clinic

Please arrive 10 minutes before your scheduled time.

CONFIRMATION REQUIRED
=====================
To confirm your appointment, simply reply to this email with "CONFIRM" in the subject line.
To reschedule or cancel, reply with "CANCEL" and your preferred time.

---
This is an automated message. Please do not reply to this email address.
"""


def main():
    """Main entry point for running the watcher."""
    vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
    check_interval = int(os.getenv("ODOO_APPOINTMENT_POLL_INTERVAL", "60"))
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    watcher = OdooAppointmentWatcher(
        vault_path=vault_path,
        check_interval=check_interval,
        api_base_url=api_base_url
    )

    try:
        logger.info("Starting Odoo Appointment Watcher...")
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Stopping Odoo Appointment Watcher...")
        watcher.stop()


if __name__ == "__main__":
    main()
