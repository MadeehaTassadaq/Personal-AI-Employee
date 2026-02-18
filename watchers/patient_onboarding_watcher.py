"""Patient Onboarding Watcher - Auto-creates patients from new WhatsApp contacts.

This watcher monitors WhatsApp webhook for new messages from unknown numbers
and automatically creates patient records in Odoo with a welcome message.

Usage:
    python -m watchers.patient_onboarding_watcher

Or via PM2:
    pm2 start watchers/patient_onboarding_watcher.py --interpreter python3 --name patient-onboarding
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
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


class PatientOnboardingWatcher(BaseWatcher):
    """Watcher for auto-onboarding new patients from WhatsApp messages.

    Features:
    - Monitors vault for new WhatsApp message indicators
    - Extracts phone number from sender
    - Queries Odoo to check if patient exists
    - Creates new patient if not found
    - Sends welcome message via WhatsApp
    - Logs all actions to audit trail
    """

    # Welcome message template
    WELCOME_MESSAGE = """🏥 *Welcome to Our Clinic!*

Thank you for reaching out. You've been registered in our healthcare system.

To complete your profile, please provide:
- Full name
- Date of birth
- Any allergies or medical conditions

Reply HELP to see available services.

---
This is an automated message.
"""

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 30,
        api_base_url: str = None
    ):
        """Initialize the patient onboarding watcher.

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Seconds between checks (default: 30)
            api_base_url: Base URL for healthcare API
        """
        super().__init__(vault_path, check_interval)

        # Configuration
        self.api_base_url = api_base_url or os.getenv(
            "API_BASE_URL",
            "http://localhost:8000"
        )
        self.enabled = os.getenv("AUTO_ONBOARD_PATIENTS", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # Tracking
        self.processed_numbers: set[str] = set()
        self._load_processed_numbers()

        logger.info(f"PatientOnboardingWatcher initialized (interval={check_interval}s, enabled={self.enabled})")

    def _load_processed_numbers(self) -> None:
        """Load processed phone numbers from disk."""
        tracking_file = self.vault_path / "data" / "onboarded_patients.json"
        if tracking_file.exists():
            try:
                data = json.loads(tracking_file.read_text())
                self.processed_numbers = set(data.get("phone_numbers", []))
                logger.info(f"Loaded {len(self.processed_numbers)} processed phone numbers")
            except Exception as e:
                logger.warning(f"Could not load processed numbers: {e}")

    def _save_processed_numbers(self) -> None:
        """Save processed phone numbers to disk."""
        tracking_file = self.vault_path / "data" / "onboarded_patients.json"
        tracking_file.parent.mkdir(parents=True, exist_ok=True)

        # Keep only last 1000
        recent_numbers = list(self.processed_numbers)[-1000:]

        data = {"phone_numbers": recent_numbers, "updated_at": datetime.now().isoformat()}
        tracking_file.write_text(json.dumps(data, indent=2))

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check for new WhatsApp messages from unknown numbers.

        This implementation checks the vault's Done/ folder for recent
        WhatsApp interactions to extract phone numbers.

        Returns:
            List of new phone numbers to process
        """
        if not self.enabled:
            return []

        try:
            # Check for recent WhatsApp task files in Done/
            done_dir = self.vault_path / "Done"
            if not done_dir.exists():
                return []

            # Look for recent WhatsApp task files
            new_numbers = []
            cutoff_time = time.time() - (24 * 3600)  # Last 24 hours

            for task_file in done_dir.glob("*whatsapp*.md"):
                # Check file modification time
                if task_file.stat().st_mtime < cutoff_time:
                    continue

                try:
                    content = task_file.read_text()

                    # Extract phone number from content
                    # Look for patterns like "phone: +1234567890" or "from: +1234567890"
                    import re
                    phone_matches = re.findall(r'[\s\":](\+\d{10,15})', content)

                    for phone in phone_matches:
                        phone = phone.strip()
                        if phone not in self.processed_numbers:
                            new_numbers.append({"phone": phone, "source": str(task_file.name)})

                except Exception as e:
                    logger.debug(f"Error reading file {task_file}: {e}")

            # Also check the WhatsApp queue for recent activity
            queue_file = self.vault_path / ".whatsapp_queue.json"
            if queue_file.exists():
                try:
                    queue_data = json.loads(queue_file.read_text())
                    for msg in queue_data.get("messages", []):
                        phone = msg.get("phone", "").strip()
                        if phone and phone not in self.processed_numbers:
                            new_numbers.append({"phone": phone, "source": "queue"})
                except Exception as e:
                    logger.debug(f"Error reading queue: {e}")

            if new_numbers:
                logger.info(f"Found {len(new_numbers)} new phone numbers to process")

            return new_numbers

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return []

    def on_new_item(self, item: Dict[str, Any]) -> None:
        """Handle a new phone number by checking if patient exists and creating if not.

        Args:
            item: Dict with 'phone' and optional 'source' keys
        """
        phone = item.get("phone", "").strip()
        if not phone:
            return

        # Normalize phone number
        if not phone.startswith("+"):
            phone = "+" + phone

        try:
            # Check if patient exists in Odoo
            patient = self._get_patient_by_phone(phone)

            if patient:
                logger.info(f"Patient already exists for phone {phone}: {patient.get('name')}")
                self.processed_numbers.add(phone)
                self._save_processed_numbers()
                return

            # Create new patient
            logger.info(f"Creating new patient for phone: {phone}")

            if self.dry_run:
                logger.info(f"DRY_RUN: Would create patient for {phone}")
                success = True
                patient_id = "DRY_RUN_ID"
            else:
                patient_id = self._create_patient_from_phone(phone)
                success = patient_id is not None

            # Send welcome message
            if success:
                self._send_welcome_message(phone)

            # Mark as processed
            self.processed_numbers.add(phone)
            self._save_processed_numbers()

            # Log event
            self.log_event("patient_onboarded", {
                "phone": phone,
                "patient_id": patient_id,
                "success": success,
                "dry_run": self.dry_run,
                "source": item.get("source", "unknown")
            })

        except Exception as e:
            logger.error(f"Error processing phone {phone}: {e}")
            self.log_event("patient_onboarding_failed", {
                "phone": phone,
                "error": str(e)
            })

    def _get_patient_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get patient by phone number from Odoo.

        Args:
            phone: Phone number with country code

        Returns:
            Patient dict or None if not found
        """
        try:
            response = httpx.get(
                f"{self.api_base_url}/api/healthcare/patients",
                params={"phone": phone},
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                patients = data.get("patients", [])
                if patients:
                    return patients[0]

            return None

        except Exception as e:
            logger.error(f"Error fetching patient by phone: {e}")
            return None

    def _create_patient_from_phone(self, phone: str) -> Optional[int]:
        """Create a new patient record with minimal info.

        Args:
            phone: Phone number with country code

        Returns:
            New patient ID or None if failed
        """
        try:
            # Generate a placeholder name from phone number
            placeholder_name = f"New Patient ({phone[-4:]})"

            response = httpx.post(
                f"{self.api_base_url}/api/healthcare/patients",
                json={
                    "name": placeholder_name,
                    "phone": phone,
                    "email": f"patient_{phone.replace('+', '')}@temp.com",  # Placeholder email
                    "date_of_birth": "1900-01-01",  # Placeholder DOB
                    "blood_type": "unknown",
                    "allergies": "",
                    "chronic_conditions": "",
                    "pregnancy_status": "not_applicable",
                    "risk_category": "low"
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                patient_id = data.get("id")
                logger.info(f"Created patient {patient_id} for phone {phone}")
                return patient_id
            else:
                logger.warning(f"Failed to create patient: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            return None

    def _send_welcome_message(self, phone: str) -> None:
        """Send welcome message to new patient.

        Args:
            phone: Phone number with country code
        """
        if self.dry_run:
            logger.info(f"DRY_RUN: Would send welcome message to {phone}")
            return

        try:
            response = httpx.post(
                f"{self.api_base_url}/api/healthcare/whatsapp/send",
                json={
                    "phone": phone,
                    "message": self.WELCOME_MESSAGE
                },
                timeout=30.0
            )

            if response.status_code == 200:
                logger.info(f"Welcome message sent to {phone}")
            else:
                logger.warning(f"Failed to send welcome: {response.status_code}")

        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")


def main():
    """Main entry point for running the watcher."""
    vault_path = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
    check_interval = int(os.getenv("PATIENT_ONBOARDING_CHECK_INTERVAL", "30"))
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    watcher = PatientOnboardingWatcher(
        vault_path=vault_path,
        check_interval=check_interval,
        api_base_url=api_base_url
    )

    try:
        logger.info("Starting Patient Onboarding Watcher...")
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Stopping Patient Onboarding Watcher...")
        watcher.stop()


if __name__ == "__main__":
    main()
