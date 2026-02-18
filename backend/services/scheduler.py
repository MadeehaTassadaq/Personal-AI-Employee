"""Scheduler service for periodic tasks and appointment confirmations."""

import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)


# ================================
# Appointment Confirmation Classes
# ================================

@dataclass
class AppointmentConfirmation:
    """Data class for appointment confirmation details."""
    appointment_id: int
    patient_id: int
    patient_name: str
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    appointment_date: str = ""
    appointment_time: str = ""
    doctor_name: str = ""
    location: str = ""
    appointment_type: str = "consultation"
    preparation_instructions: str = ""
    channel_preference: str = "whatsapp"  # whatsapp or email


class ConfirmationService:
    """Service for sending appointment confirmations via WhatsApp/Email."""

    def __init__(self):
        self.confirmation_queue: List[Dict[str, Any]] = []
        self.delivery_status: Dict[int, Dict[str, Any]] = {}
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min in seconds
        self._auto_approve_enabled = os.getenv("AUTO_CONFIRM_APPOINTMENTS", "true").lower() == "true"

    def generate_confirmation_message(self, confirmation: AppointmentConfirmation, channel: str) -> str:
        """Generate confirmation message based on channel (WhatsApp or Email).

        Args:
            confirmation: Appointment confirmation details
            channel: 'whatsapp' or 'email'

        Returns:
            Formatted confirmation message
        """
        if channel == "whatsapp":
            return self._generate_whatsapp_confirmation(confirmation)
        else:
            return self._generate_email_confirmation(confirmation)

    def _generate_whatsapp_confirmation(self, confirmation: AppointmentConfirmation) -> str:
        """Generate WhatsApp-formatted confirmation message."""
        emoji_map = {
            "consultation": "🩺",
            "followup": "🔄",
            "checkup": "🏥",
            "emergency": "🚨",
            "prenatal": "🤰",
            "lab_test": "🧪"
        }
        emoji = emoji_map.get(confirmation.appointment_type, "📅")

        message = f"""{emoji} *Appointment Confirmed*

Dear {confirmation.patient_name},

Your appointment has been scheduled:

📅 *Date:* {confirmation.appointment_date}
⏰ *Time:* {confirmation.appointment_time}
👨‍⚕️ *Doctor:* {confirmation.doctor_name}
📍 *Location:* {confirmation.location}
"""

        if confirmation.preparation_instructions:
            message += f"📝 *Instructions:* {confirmation.preparation_instructions}\n\n"

        message += """Please arrive 10 minutes early.
Reply CONFIRM to confirm or CANCEL to reschedule.

***This is an automated message. For emergencies, call the clinic directly."""

        return message

    def _generate_email_confirmation(self, confirmation: AppointmentConfirmation) -> str:
        """Generate email-formatted confirmation message."""
        subject = f"Appointment Confirmation - {confirmation.appointment_date}"

        body = f"""Dear {confirmation.patient_name},

Your appointment has been successfully scheduled.

APPOINTMENT DETAILS
===================
Date: {confirmation.appointment_date}
Time: {confirmation.appointment_time}
Doctor: {confirmation.doctor_name}
Location: {confirmation.location}
Type: {confirmation.appointment_type.title()}
"""

        if confirmation.preparation_instructions:
            body += f"""
PREPARATION INSTRUCTIONS
========================
{confirmation.preparation_instructions}
"""

        body += """
Please arrive 10 minutes before your scheduled time.

CONFIRMATION REQUIRED
=====================
To confirm your appointment, simply reply to this email with "CONFIRM" in the subject line.
To reschedule or cancel, reply with "CANCEL" and your preferred time.

CONTACT INFORMATION
===================
For questions or emergencies, please contact the clinic directly.

---
This is an automated message. Please do not reply to this email address.
"""

        return body

    async def send_confirmation(
        self,
        confirmation: AppointmentConfirmation,
        dry_run: bool = None
    ) -> Dict[str, Any]:
        """Send appointment confirmation via patient's preferred channel.

        Creates a vault task file for approval instead of sending directly.

        Args:
            confirmation: Appointment confirmation details
            dry_run: Override DRY_RUN setting if provided

        Returns:
            Dict with delivery status, message_id, and retry info
        """
        if dry_run is None:
            dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # Determine channel
        channel = confirmation.channel_preference
        if channel == "whatsapp" and not confirmation.patient_phone:
            if confirmation.patient_email:
                channel = "email"
                logger.info(f"Falling back to email for appointment {confirmation.appointment_id}")
            else:
                return {
                    "success": False,
                    "error": "No contact method available",
                    "retry": False
                }

        if channel == "email" and not confirmation.patient_email:
            if confirmation.patient_phone:
                channel = "whatsapp"
                logger.info(f"Falling back to WhatsApp for appointment {confirmation.appointment_id}")
            else:
                return {
                    "success": False,
                    "error": "No contact method available",
                    "retry": False
                }

        # Generate message
        message = self.generate_confirmation_message(confirmation, channel)

        # Create vault task file for approval
        vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
        pending_approval_dir = vault_path / "Pending_Approval"
        pending_approval_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-appointment-confirmation-{confirmation.appointment_id}.md"

        # Create the task file content
        content = f"""---
title: "Appointment Confirmation for {confirmation.patient_name}"
created: {datetime.now().isoformat()}
priority: normal
status: pending_approval
type: whatsapp
platform: whatsapp
channel: {channel}
recipient: "{confirmation.patient_phone if channel == 'whatsapp' else confirmation.patient_email}"
appointment_id: {confirmation.appointment_id}
patient_id: {confirmation.patient_id}
patient_name: "{confirmation.patient_name}"
appointment_date: "{confirmation.appointment_date}"
appointment_time: "{confirmation.appointment_time}"
doctor_name: "{confirmation.doctor_name}"
location: "{confirmation.location}"
appointment_type: "{confirmation.appointment_type}"
assignee: claude
tags: [healthcare, appointment, confirmation]
requires_approval: true
---

# Appointment Confirmation

## Patient Details
- **Name:** {confirmation.patient_name}
- **Patient ID:** {confirmation.patient_id}
- **Appointment ID:** {confirmation.appointment_id}

## Appointment Details
- **Date:** {confirmation.appointment_date}
- **Time:** {confirmation.appointment_time}
- **Doctor:** {confirmation.doctor_name}
- **Location:** {confirmation.location}
- **Type:** {confirmation.appointment_type}

## Channel
{channel.upper()} → {confirmation.patient_phone if channel == 'whatsapp' else confirmation.patient_email}

### Message Content

{message}

## Action Required
- [ ] Review confirmation message
- [ ] Approve to send {channel} message
- [ ] Reject to cancel sending

## Notes
This is an automated appointment confirmation message that requires approval before being sent to the patient.
"""

        if dry_run:
            logger.info(f"DRY_RUN: Would create approval task for appointment {confirmation.appointment_id}")
            return {
                "success": True,
                "channel": channel,
                "dry_run": True,
                "appointment_id": confirmation.appointment_id,
                "task_file": str(pending_approval_dir / filename)
            }

        try:
            # Write the task file to Pending_Approval
            task_path = pending_approval_dir / filename
            task_path.write_text(content)

            logger.info(f"Created approval task for appointment confirmation: {filename}")

            # Update delivery status
            self.delivery_status[confirmation.appointment_id] = {
                "channel": channel,
                "created_at": datetime.now().isoformat(),
                "status": "pending_approval",
                "task_file": str(task_path),
                "retry_count": 0
            }

            return {
                "success": True,
                "channel": channel,
                "appointment_id": confirmation.appointment_id,
                "task_file": str(task_path),
                "status": "pending_approval",
                "message": f"Confirmation created for approval at: {task_path}"
            }

        except Exception as e:
            logger.error(f"Failed to create approval task for appointment {confirmation.appointment_id}: {e}")
            self.delivery_status[confirmation.appointment_id] = {
                "channel": channel,
                "created_at": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e),
                "retry_count": 0
            }
            return {
                "success": False,
                "error": str(e),
                "retry": True,
                "appointment_id": confirmation.appointment_id
            }

    async def _send_whatsapp(self, phone: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message via MCP server."""
        try:
            # Import here to avoid circular dependency
            import sys
            from pathlib import Path
            mcp_path = Path(os.getcwd()).parent / "mcp_services/whatsapp_mcp"
            if str(mcp_path) not in sys.path:
                sys.path.insert(0, str(mcp_path))

            # TODO: Integrate with actual MCP server
            # from tools import WHATSAPP_TOOLS
            logger.info(f"Sending WhatsApp message to {phone}")
            return {"success": True, "message_id": f"wa_{datetime.now().timestamp()}"}
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_email(self, email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email via MCP server."""
        try:
            # Import here to avoid circular dependency
            import sys
            from pathlib import Path
            mcp_path = Path(os.getcwd()).parent / "mcp_services/gmail_mcp"
            if str(mcp_path) not in sys.path:
                sys.path.insert(0, str(mcp_path))

            # TODO: Integrate with actual MCP server
            # from tools import GMAIL_TOOLS
            logger.info(f"Sending email to {email}")
            return {"success": True, "message_id": f"email_{datetime.now().timestamp()}"}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"success": False, "error": str(e)}

    async def retry_confirmation(self, appointment_id: int) -> Dict[str, Any]:
        """Retry sending confirmation with exponential backoff.

        Args:
            appointment_id: Appointment ID to retry

        Returns:
            Dict with retry result
        """
        if appointment_id not in self.delivery_status:
            return {"success": False, "error": "No previous delivery attempt found"}

        status = self.delivery_status[appointment_id]
        retry_count = status.get("retry_count", 0)

        if retry_count >= self.max_retries:
            return {
                "success": False,
                "error": "Max retries exceeded",
                "retry_count": retry_count
            }

        # Calculate delay
        delay = self.retry_delays[min(retry_count, len(self.retry_delays) - 1)]
        last_sent = status.get("sent_at")

        if last_sent:
            last_sent_time = datetime.fromisoformat(last_sent)
            if datetime.now() - last_sent_time < timedelta(seconds=delay):
                wait_time = delay - (datetime.now() - last_sent_time).total_seconds()
                return {
                    "success": False,
                    "error": f"Retry not available yet. Wait {int(wait_time)} seconds.",
                    "retry_available_at": (last_sent_time + timedelta(seconds=delay)).isoformat()
                }

        # TODO: Implement actual retry with stored confirmation details
        status["retry_count"] = retry_count + 1
        return {"success": True, "retry_count": retry_count + 1}

    def get_delivery_status(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        """Get delivery status for an appointment confirmation.

        Args:
            appointment_id: Appointment ID

        Returns:
            Delivery status dict or None if not found
        """
        return self.delivery_status.get(appointment_id)

    def add_to_queue(self, confirmation: AppointmentConfirmation):
        """Add confirmation to queue for batch processing.

        Args:
            confirmation: Appointment confirmation details
        """
        self.confirmation_queue.append({
            "confirmation": confirmation,
            "queued_at": datetime.now().isoformat(),
            "priority": "high" if confirmation.appointment_type == "emergency" else "normal"
        })

    async def process_queue(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Process confirmation queue in batches.

        Args:
            batch_size: Number of confirmations to process

        Returns:
            List of delivery results
        """
        results = []
        batch = self.confirmation_queue[:batch_size]
        self.confirmation_queue = self.confirmation_queue[batch_size:]

        for item in batch:
            confirmation = item["confirmation"]
            result = await self.send_confirmation(confirmation)
            results.append(result)

        return results

    async def send_confirmation_auto(
        self,
        confirmation: AppointmentConfirmation,
        dry_run: bool = None
    ) -> Dict[str, Any]:
        """Send appointment confirmation directly without approval workflow.

        This method bypasses the vault approval system and sends confirmations
        automatically. Only use for routine appointment confirmations.

        Args:
            confirmation: Appointment confirmation details
            dry_run: Override DRY_RUN setting if provided

        Returns:
            Dict with delivery status, message_id, and retry info
        """
        if dry_run is None:
            dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        if not self._auto_approve_enabled:
            # Fall back to approval workflow if auto-approve is disabled
            logger.info(f"Auto-approval disabled, using approval workflow for appointment {confirmation.appointment_id}")
            return await self.send_confirmation(confirmation, dry_run)

        # Determine channel
        channel = confirmation.channel_preference
        if channel == "whatsapp" and not confirmation.patient_phone:
            if confirmation.patient_email:
                channel = "email"
                logger.info(f"Falling back to email for appointment {confirmation.appointment_id}")
            else:
                return {
                    "success": False,
                    "error": "No contact method available",
                    "auto_approved": False
                }

        if channel == "email" and not confirmation.patient_email:
            if confirmation.patient_phone:
                channel = "whatsapp"
                logger.info(f"Falling back to WhatsApp for appointment {confirmation.appointment_id}")
            else:
                return {
                    "success": False,
                    "error": "No contact method available",
                    "auto_approved": False
                }

        # Generate message
        message = self.generate_confirmation_message(confirmation, channel)

        result = {
            "appointment_id": confirmation.appointment_id,
            "channel": channel,
            "auto_approved": True,
            "dry_run": dry_run,
            "sent_at": datetime.now().isoformat()
        }

        if dry_run:
            logger.info(f"DRY_RUN: Would send auto-approval confirmation to {confirmation.patient_name}")
            result["success"] = True
            result["dry_run"] = True
        else:
            # Send via appropriate channel
            try:
                if channel == "whatsapp":
                    send_result = await self._send_whatsapp_direct(confirmation.patient_phone, message)
                else:
                    send_result = await self._send_email_direct(
                        confirmation.patient_email,
                        f"Appointment Confirmation - {confirmation.appointment_date}",
                        message
                    )
                result["success"] = send_result.get("success", False)
                result["message_id"] = send_result.get("message_id")

                # Log auto-action to audit trail
                self._log_auto_action(
                    action_type="appointment_confirmation",
                    channel=channel,
                    recipient=confirmation.patient_phone if channel == "whatsapp" else confirmation.patient_email,
                    appointment_id=confirmation.appointment_id,
                    success=result["success"]
                )

            except Exception as e:
                logger.error(f"Failed to send auto-confirmation: {e}")
                result["success"] = False
                result["error"] = str(e)

        # Update delivery status
        self.delivery_status[confirmation.appointment_id] = {
            "channel": channel,
            "created_at": datetime.now().isoformat(),
            "status": "sent" if result.get("success") else "failed",
            "auto_approved": True,
            "retry_count": 0
        }

        return result

    def _log_auto_action(self, action_type: str, channel: str, recipient: str,
                        appointment_id: int, success: bool) -> None:
        """Log auto-approved action to audit trail.

        Args:
            action_type: Type of auto-action (e.g., "appointment_confirmation")
            channel: Communication channel (whatsapp/email)
            recipient: Recipient contact
            appointment_id: Associated appointment ID
            success: Whether the action succeeded
        """
        import json
        vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
        log_dir = vault_path / "Logs"
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": "ConfirmationService",
            "event": "auto_action",
            "action_type": action_type,
            "channel": channel,
            "recipient": recipient,
            "appointment_id": appointment_id,
            "success": success,
            "auto_approved": True
        }

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps(logs, indent=2))

    async def _send_whatsapp_direct(self, phone: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message directly via Publisher.

        Args:
            phone: Phone number with country code
            message: Message content

        Returns:
            Send result with success status and message_id
        """
        try:
            from .publisher import get_publisher
            publisher = get_publisher()
            return await publisher.send_whatsapp(message, phone)
        except Exception as e:
            logger.error(f"Direct WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_email_direct(self, email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email directly via Publisher.

        Args:
            email: Email address
            subject: Email subject
            body: Email body

        Returns:
            Send result with success status and message_id
        """
        try:
            from .publisher import get_publisher
            publisher = get_publisher()
            return await publisher.send_email(body, email, subject)
        except Exception as e:
            logger.error(f"Direct email send failed: {e}")
            return {"success": False, "error": str(e)}


# ================================
# Reminder Service Classes
# ================================

@dataclass
class ReminderSchedule:
    """Configuration for appointment reminders."""
    appointment_id: int
    patient_id: int
    patient_name: str
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    appointment_date: str = ""
    appointment_time: str = ""
    doctor_name: str = ""
    location: str = ""
    channel_preference: str = "whatsapp"
    hours_before_appointment: List[int] = None  # e.g., [24, 2] for 24h and 2h reminders

    def __post_init__(self):
        if self.hours_before_appointment is None:
            self.hours_before_appointment = [24, 2]


class ReminderService:
    """Service for sending appointment reminders."""

    # Reminder tracking file
    SENT_REMINDERS_FILE = "AI_Employee_Vault/data/sent_reminders.json"

    def __init__(self):
        self.reminder_queue: List[ReminderSchedule] = []
        self.sent_reminders: Dict[int, List[Dict[str, Any]]] = {}  # appointment_id -> list of sent reminders
        self.reminder_intervals = [24, 2]  # hours before appointment
        self._load_sent_reminders()
        self._auto_approve_enabled = os.getenv("AUTO_REMINDERS_ENABLED", "true").lower() == "true"
        self._rate_limit_last_send = 0
        self._rate_limit_min_interval = 1.0  # 1 second between sends

    def _load_sent_reminders(self) -> None:
        """Load sent reminders from persistent storage."""
        import json
        try:
            reminders_file = Path(self.SENT_REMINDERS_FILE)
            if reminders_file.exists():
                data = json.loads(reminders_file.read_text())
                # Convert list to dict by appointment_id
                for entry in data.get("reminders", []):
                    appt_id = entry.get("appointment_id")
                    if appt_id is not None:
                        if appt_id not in self.sent_reminders:
                            self.sent_reminders[appt_id] = []
                        self.sent_reminders[appt_id].append(entry)
                logger.info(f"Loaded {len(self.sent_reminders)} appointments with sent reminders")
        except Exception as e:
            logger.warning(f"Could not load sent reminders: {e}")

    def _save_sent_reminders(self) -> None:
        """Save sent reminders to persistent storage."""
        import json
        try:
            reminders_file = Path(self.SENT_REMINDERS_FILE)
            reminders_file.parent.mkdir(parents=True, exist_ok=True)

            # Flatten dict to list
            all_reminders = []
            for appt_id, reminders in self.sent_reminders.items():
                for reminder in reminders:
                    reminder["appointment_id"] = appt_id
                    all_reminders.append(reminder)

            # Keep only last 1000 reminders
            all_reminders = sorted(all_reminders, key=lambda x: x.get("sent_at", ""), reverse=True)[:1000]

            data = {"reminders": all_reminders}
            reminders_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Could not save sent reminders: {e}")

    def _reminder_already_sent(self, appointment_id: int, hours_before: int) -> bool:
        """Check if reminder was already sent for this appointment/time.

        Args:
            appointment_id: Appointment ID
            hours_before: Hours before appointment

        Returns:
            True if reminder was already sent
        """
        if appointment_id not in self.sent_reminders:
            return False

        for sent in self.sent_reminders[appointment_id]:
            if sent.get("hours_before") == hours_before:
                # Check if sent in last 48 hours (allow re-sending for recurring appointments)
                try:
                    sent_at = datetime.fromisoformat(sent.get("sent_at", ""))
                    if (datetime.now() - sent_at).total_seconds() < 48 * 3600:
                        return True
                except:
                    pass
        return False

    def _track_reminder_sent(self, appointment_id: int, hours_before: int, channel: str, success: bool) -> None:
        """Track that a reminder was sent.

        Args:
            appointment_id: Appointment ID
            hours_before: Hours before appointment
            channel: Communication channel
            success: Whether send succeeded
        """
        if appointment_id not in self.sent_reminders:
            self.sent_reminders[appointment_id] = []

        self.sent_reminders[appointment_id].append({
            "hours_before": hours_before,
            "channel": channel,
            "success": success,
            "sent_at": datetime.now().isoformat()
        })

        # Persist to disk
        self._save_sent_reminders()

    def generate_reminder_message(self, reminder: ReminderSchedule, hours_before: int, channel: str) -> str:
        """Generate reminder message based on channel and timing.

        Args:
            reminder: Reminder details
            hours_before: Hours before appointment
            channel: 'whatsapp' or 'email'

        Returns:
            Formatted reminder message
        """
        if channel == "whatsapp":
            return self._generate_whatsapp_reminder(reminder, hours_before)
        else:
            return self._generate_email_reminder(reminder, hours_before)

    def _generate_whatsapp_reminder(self, reminder: ReminderSchedule, hours_before: int) -> str:
        """Generate WhatsApp reminder message."""
        urgency_emoji = "⏰" if hours_before > 2 else "🔔"

        message = f"""{urgency_emoji} *Appointment Reminder*

Dear {reminder.patient_name},

This is a reminder about your upcoming appointment:

📅 *Date:* {reminder.appointment_date}
⏰ *Time:* {reminder.appointment_time}
👨‍⚕️ *Doctor:* {reminder.doctor_name}
📍 *Location:* {reminder.location}

Your appointment is in {hours_before} hour{'s' if hours_before != 1 else ''}.

Reply CONFIRM to confirm your attendance.
Reply CANCEL if you need to reschedule.

---
This is an automated message."""
        return message

    def _generate_email_reminder(self, reminder: ReminderSchedule, hours_before: int) -> str:
        """Generate email reminder message."""
        body = f"""Dear {reminder.patient_name},

This is a friendly reminder about your upcoming appointment.

APPOINTMENT DETAILS
===================
Date: {reminder.appointment_date}
Time: {reminder.appointment_time}
Doctor: {reminder.doctor_name}
Location: {reminder.location}

Your appointment is in {hours_before} hour{'s' if hours_before != 1 else ''}.

CONFIRMATION REQUIRED
=====================
Please confirm your attendance by replying with "CONFIRM".
If you need to reschedule or cancel, please reply with "CANCEL".

---
This is an automated message. Please do not reply to this email address.
"""
        return body

    async def schedule_reminders(self, appointments: List[Dict[str, Any]]) -> int:
        """Schedule reminders for upcoming appointments.

        Args:
            appointments: List of appointment dicts with patient and doctor details

        Returns:
            Number of reminders scheduled
        """
        scheduled = 0
        from datetime import datetime, timedelta

        for appointment in appointments:
            appointment_id = appointment.get("id")
            if not appointment_id:
                continue

            # Skip if already fully reminded
            if appointment_id in self.sent_reminders:
                sent_count = len(self.sent_reminders[appointment_id])
                if sent_count >= len(self.reminder_intervals):
                    continue

            # Parse appointment date/time
            appt_str = appointment.get("appointment_date")
            if not appt_str:
                continue

            try:
                appt_datetime = datetime.fromisoformat(appt_str.replace("Z", "+00:00"))
            except:
                continue

            # Create reminder schedule
            patient = appointment.get("patient", {})
            reminder = ReminderSchedule(
                appointment_id=appointment_id,
                patient_id=appointment.get("patient_id", 0),
                patient_name=patient.get("name", ""),
                patient_phone=patient.get("phone"),
                patient_email=patient.get("email"),
                appointment_date=appt_datetime.strftime("%Y-%m-%d"),
                appointment_time=appt_datetime.strftime("%I:%M %p"),
                doctor_name=appointment.get("doctor", {}).get("name", ""),
                location=appointment.get("location", "Main Clinic"),
                channel_preference="whatsapp" if patient.get("phone") else "email",
                hours_before_appointment=self.reminder_intervals
            )

            self.reminder_queue.append(reminder)
            scheduled += 1

        logger.info(f"Scheduled {scheduled} appointment reminders")
        return scheduled

    async def send_reminders(self, dry_run: bool = None) -> List[Dict[str, Any]]:
        """Send due reminders from the queue.

        Args:
            dry_run: Override DRY_RUN setting

        Returns:
            List of delivery results
        """
        if dry_run is None:
            dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        if not self._auto_approve_enabled:
            logger.info("Auto-reminders disabled, skipping")
            return []

        results = []
        from datetime import datetime, timedelta

        for reminder in self.reminder_queue[:]:  # Copy to iterate
            appt_datetime = datetime.strptime(f"{reminder.appointment_date} {reminder.appointment_time}", "%Y-%m-%d %I:%M %p")
            now = datetime.now()

            # Check each reminder interval
            for hours_before in reminder.hours_before_appointment:
                # Calculate when this reminder should be sent
                reminder_time = appt_datetime - timedelta(hours=hours_before)

                # Check if it's time to send (within 5 minutes)
                if abs((now - reminder_time).total_seconds()) < 300:
                    # Check if already sent using tracking method
                    if self._reminder_already_sent(reminder.appointment_id, hours_before):
                        continue

                    # Generate and send message
                    channel = reminder.channel_preference
                    message = self.generate_reminder_message(reminder, hours_before, channel)

                    result = {
                        "appointment_id": reminder.appointment_id,
                        "hours_before": hours_before,
                        "channel": channel,
                        "auto_approved": True,
                        "dry_run": dry_run,
                        "sent_at": now.isoformat()
                    }

                    if dry_run:
                        logger.info(f"DRY_RUN: Would send {hours_before}h reminder to {reminder.patient_name}")
                        result["success"] = True
                        # Still track in dry run mode for testing
                        self._track_reminder_sent(reminder.appointment_id, hours_before, channel, True)
                    else:
                        # Rate limiting: wait if needed
                        elapsed = time.time() - self._rate_limit_last_send
                        if elapsed < self._rate_limit_min_interval:
                            await asyncio.sleep(self._rate_limit_min_interval - elapsed)

                        # Send via appropriate channel using direct methods
                        try:
                            if channel == "whatsapp":
                                send_result = await self._send_whatsapp_direct(reminder.patient_phone, message)
                            else:
                                send_result = await self._send_email_direct(
                                    reminder.patient_email,
                                    f"Appointment Reminder - {reminder.appointment_date}",
                                    message
                                )
                            result["success"] = send_result.get("success", False)
                            result["message_id"] = send_result.get("message_id")

                            # Track sent reminder
                            self._track_reminder_sent(reminder.appointment_id, hours_before, channel, result["success"])

                            # Log auto-action to audit trail
                            self._log_auto_action(
                                action_type="appointment_reminder",
                                channel=channel,
                                recipient=reminder.patient_phone if channel == "whatsapp" else reminder.patient_email,
                                appointment_id=reminder.appointment_id,
                                hours_before=hours_before,
                                success=result["success"]
                            )

                            self._rate_limit_last_send = time.time()

                        except Exception as e:
                            logger.error(f"Failed to send reminder: {e}")
                            result["success"] = False
                            result["error"] = str(e)
                            # Track failed send
                            self._track_reminder_sent(reminder.appointment_id, hours_before, channel, False)

                    results.append(result)

        return results

    def _log_auto_action(self, action_type: str, channel: str, recipient: str,
                        appointment_id: int, hours_before: int = None, success: bool = True) -> None:
        """Log auto-approved reminder action to audit trail.

        Args:
            action_type: Type of auto-action (e.g., "appointment_reminder")
            channel: Communication channel (whatsapp/email)
            recipient: Recipient contact
            appointment_id: Associated appointment ID
            hours_before: Hours before appointment (for reminders)
            success: Whether the action succeeded
        """
        import json
        vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
        log_dir = vault_path / "Logs"
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": "ReminderService",
            "event": "auto_action",
            "action_type": action_type,
            "channel": channel,
            "recipient": recipient,
            "appointment_id": appointment_id,
            "success": success,
            "auto_approved": True
        }

        if hours_before is not None:
            log_entry["hours_before"] = hours_before

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps(logs, indent=2))

    async def _send_whatsapp_direct(self, phone: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message directly via Publisher.

        Args:
            phone: Phone number with country code
            message: Message content

        Returns:
            Send result with success status and message_id
        """
        try:
            from .publisher import get_publisher
            publisher = get_publisher()
            return await publisher.send_whatsapp(message, phone)
        except Exception as e:
            logger.error(f"Direct WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_email_direct(self, email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email directly via Publisher.

        Args:
            email: Email address
            subject: Email subject
            body: Email body

        Returns:
            Send result with success status and message_id
        """
        try:
            from .publisher import get_publisher
            publisher = get_publisher()
            return await publisher.send_email(body, email, subject)
        except Exception as e:
            logger.error(f"Direct email send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_whatsapp(self, phone: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message via MCP server."""
        try:
            # Import here to avoid circular dependency
            import sys
            from pathlib import Path
            mcp_path = Path(os.getcwd()).parent / "mcp_services/whatsapp_mcp"
            if str(mcp_path) not in sys.path:
                sys.path.insert(0, str(mcp_path))

            # TODO: Integrate with actual MCP server
            logger.info(f"Sending WhatsApp reminder to {phone}")
            return {"success": True, "message_id": f"wa_reminder_{datetime.now().timestamp()}"}
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_email(self, email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email via MCP server."""
        try:
            # Import here to avoid circular dependency
            import sys
            from pathlib import Path
            mcp_path = Path(os.getcwd()).parent / "mcp_services/gmail_mcp"
            if str(mcp_path) not in sys.path:
                sys.path.insert(0, str(mcp_path))

            # TODO: Integrate with actual MCP server
            logger.info(f"Sending email reminder to {email}")
            return {"success": True, "message_id": f"email_reminder_{datetime.now().timestamp()}"}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"success": False, "error": str(e)}

    def get_reminder_status(self, appointment_id: int) -> Dict[str, Any]:
        """Get reminder status for an appointment.

        Args:
            appointment_id: Appointment ID

        Returns:
            Reminder status dict
        """
        return {
            "appointment_id": appointment_id,
            "sent_reminders": self.sent_reminders.get(appointment_id, []),
            "pending_reminders": len([r for r in self.reminder_queue if r.appointment_id == appointment_id])
        }


# ================================
# Original TaskScheduler Class
# ================================

class TaskScheduler:
    """Simple scheduler for periodic tasks."""

    def __init__(self):
        self.tasks = {}
        self.running = False
        self.thread = None

    def add_periodic_task(self, name: str, func: Callable, interval: int, immediate: bool = True):
        """Add a periodic task to run every 'interval' seconds.

        Args:
            name: Unique name for the task
            func: Function to call
            interval: Interval in seconds
            immediate: Whether to run immediately on start
        """
        self.tasks[name] = {
            'func': func,
            'interval': interval,
            'last_run': time.time() if not immediate else time.time() - interval,
            'enabled': True
        }

    def remove_task(self, name: str):
        """Remove a scheduled task."""
        if name in self.tasks:
            del self.tasks[name]

    def disable_task(self, name: str):
        """Disable a scheduled task."""
        if name in self.tasks:
            self.tasks[name]['enabled'] = False

    def enable_task(self, name: str):
        """Enable a scheduled task."""
        if name in self.tasks:
            self.tasks[name]['enabled'] = True

    def _run_scheduler(self):
        """Internal method to run the scheduler loop."""
        while self.running:
            current_time = time.time()

            for name, task in self.tasks.items():
                if task['enabled'] and (current_time - task['last_run']) >= task['interval']:
                    try:
                        task['func']()
                        task['last_run'] = current_time
                    except Exception as e:
                        print(f"Error running scheduled task {name}: {e}")

            time.sleep(1)  # Sleep briefly to avoid busy waiting

    def start(self):
        """Start the scheduler."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish


# ================================
# Global Instances
# ================================

# Global scheduler instance
scheduler = TaskScheduler()

# Global confirmation service instance
confirmation_service = ConfirmationService()

# Global reminder service instance
reminder_service = ReminderService()


# ================================
# Scheduler Functions
# ================================

def init_scheduler():
    """Initialize the scheduler with default tasks."""
    # TODO: Create missing modules
    # from .dashboard_updater import update_dashboard_now
    # from .watchdog import run_watchdog_check

    # Update dashboard every 60 seconds to better align with frontend refreshes
    # scheduler.add_periodic_task(
    #     name="dashboard_update",
    #     func=update_dashboard_now,
    #     interval=60,  # Every 1 minute
    #     immediate=True
    # )

    # Run watchdog health check every 30 seconds
    # scheduler.add_periodic_task(
    #     name="watchdog_check",
    #     func=run_watchdog_check,
    #     interval=30,  # Every 30 seconds
    #     immediate=False  # Wait before first check
    # )

    # Check daily tasks every minute (inbox processing at 9 AM, meeting reminders at 8 AM)
    # Disabled: daily_checks need async event loop which doesn't work in threading scheduler
    # TODO: Migrate to APScheduler or implement async-safe scheduler
    # async def daily_check_wrapper():
    #     from .daily_scheduler import run_daily_checks
    #     await run_daily_checks()
    #
    # scheduler.add_periodic_task(
    #     name="daily_checks",
    #     func=lambda: asyncio.create_task(daily_check_wrapper()),
    #     interval=60,  # Check every minute
    #     immediate=False
    # )

    scheduler.start()


def shutdown_scheduler():
    """Shutdown the scheduler."""
    scheduler.stop()


# Convenience functions
def schedule_dashboard_update():
    """Schedule a dashboard update."""
    # TODO: Create missing module
    # from .dashboard_updater import update_dashboard_now
    # update_dashboard_now()
    pass


if __name__ == "__main__":
    # Test the scheduler
    def test_task():
        print(f"Test task executed at {datetime.now()}")

    scheduler.add_periodic_task("test", test_task, 5)
    scheduler.start()

    # Let it run for a bit
    time.sleep(20)
    scheduler.stop()
