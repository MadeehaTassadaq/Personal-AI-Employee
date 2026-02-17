"""Appointment Reminder Service for Healthcare.

Queries upcoming appointments and sends reminders via WhatsApp/Email.
"""
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Add MCP to path
mcp_path = Path(os.getcwd()) / "mcp_services/odoo_mcp"
if str(mcp_path) not in sys.path:
    sys.path.insert(0, str(mcp_path))

from mcp_services.odoo_mcp.jsonrpc_client import get_client
from mcp_services.whatsapp_mcp.server import send_message
from mcp_services.gmail_mcp.server import send_email

# Configuration
REMINDER_HOURS_AHEAD = 24
CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes

async def get_upcoming_appointments():
    """Get upcoming appointments that need reminders."""
    try:
        client = get_client()
        await client.authenticate()

        cutoff = (datetime.now() + timedelta(days=REMINDER_HOURS_AHEAD)).isoformat()
        now = datetime.now().isoformat()

        appointments = await client.search_read(
            "medical.appointment",
            [
                ("appointment_date", ">=", now),
                ("appointment_date", "<=", cutoff),
                ("status", "in", ["scheduled", "confirmed"]),
                ("reminder_sent", "=", False)
            ],
            ["id", "name", "appointment_date", "patient_id", "doctor_id"],
            limit=100,
            order="appointment_date asc"
        )

        return appointments
    except Exception as e:
        print(f"Error fetching appointments: {e}")
        return []

async def check_and_send_reminders():
    """Check upcoming appointments and send reminders."""
    print(f"[{datetime.now().isoformat()}] Checking for appointments to remind...")

    appointments = await get_upcoming_appointments()
    sent_count = 0

    for apt in appointments:
        try:
            apt_date = apt.get("appointment_date", "")
            apt_time = datetime.fromisoformat(apt_date) if isinstance(apt_date, str) else datetime.fromisoformat(apt_date[:19])

            # Calculate time until appointment (24 hours before)
            apt_datetime = datetime.combine(apt_time.date(), apt_time.time())
            reminder_time = apt_datetime - timedelta(hours=REMINDER_HOURS_AHEAD)
            now = datetime.now()

            if now >= reminder_time:
                # Time to send reminder
                patient_name = apt.get("patient_id", ["", ""])[0] if apt.get("patient_id") else apt.get("patient_id", ["Unknown"])
                patient_phone = apt.get("patient_id", ["", ""])[1] if apt.get("patient_id") else apt.get("patient_id", ["Unknown"], ""])

                message = f"""Reminder: Your appointment is scheduled for {apt_date.strftime('%A, %d %Y at %I:%M %p')}.

Doctor: {apt.get('doctor_id', ['Dr.', ''])[1] if apt.get('doctor_id') else apt.get('doctor_id', ['Dr.', 'Unknown'])[2]} {apt.get('doctor_id', ['Dr.', ''])[2] if apt.get('doctor_id') else apt.get('doctor_id', ['Dr.', 'Unknown'])[3]}

Please arrive 15 minutes early.

Type: {apt.get('appointment_type', 'Consultation', apt.get('appointment_type', 'Unknown')}

Bring your medical records if applicable.
"""
                # Check if already sent
                if apt.get("reminder_sent", False):
                    print(f"  Reminder already sent for appointment {apt.get('id')}")
                    continue

                # Send WhatsApp reminder
                try:
                    await send_message(
                        to=patient_phone,
                        text=message
                    )
                    print(f"  WhatsApp reminder sent to {patient_phone}")
                    sent_count += 1

                    # Mark as sent
                    await client.write("medical.appointment", apt.get("id"), {"reminder_sent": True, "reminder_method": "whatsapp"})
                    print(f"  Marked reminder sent for appointment {apt.get('id')}")

                except Exception as e:
                    print(f"  Error sending WhatsApp: {e}")

                # Send Email reminder
                try:
                    patient_email = apt.get("patient_id", ["", ""])[2] if apt.get("patient_id") else apt.get("patient_id", ["Unknown"], ""])[3] if len(apt.get("patient_id")) > 3 else apt.get("patient_id", ["Unknown"], ""])[3]

                    if patient_email:
                        await send_email(
                            to=patient_email,
                            subject=f"Appointment Reminder - {apt_date.strftime('%Y-%m-%d')}",
                            text=message
                        )
                        print(f"  Email reminder sent to {patient_email}")
                        sent_count += 1

                except Exception as e:
                    print(f"  Error sending email: {e}")

        except Exception as e:
        print(f"  Error processing appointments: {e}")

    return {
        "checked": datetime.now().isoformat(),
        "sent": sent_count,
        "total": len(appointments)
    }


async def send_message(to: str, text: str):
    """Send WhatsApp message using MCP."""
    try:
        from mcp_services.whatsapp_mcp.server import send_message
        await send_message(to=to, message=text)
        return {"status": "sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def send_email(to: str, subject: str, text: str):
    """Send email using MCP."""
    try:
        from mcp_services.gmail_mcp.server import send_email
        await send_email(to=to, subject=subject, text=text)
        return {"status": "sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def main():
    """Main entry point for scheduled execution."""
    print(f"Reminder Service started at {datetime.now().isoformat()}")
    print(f"Checking for appointments {REMINDER_HOURS_AHEAD} hours ahead...")

    # Run continuously
    while True:
        result = await check_and_send_reminders()
        print(f"Check completed: {result}")

        # Wait before next check
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    # Check if dry run
        dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        if dry_run:
            print("[DRY_RUN] Would send reminders, but skipping actual sends...")


if __name__ == "__main__":
    asyncio.run(main())
