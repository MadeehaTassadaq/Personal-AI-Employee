
"""Healthcare tools for Odoo MCP Server.

Extends the Odoo MCP server with healthcare-specific functionality
for patient management, appointments, vitals, and billing.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from .jsonrpc_client import get_client, OdooClient
from .server import log_action, DRY_RUN

# Import mcp server
from mcp.server import Server

# Get the app instance or create a new one
try:
    from .server import app
except ImportError:
    app = Server("odoo-mcp-healthcare")


def get_healthcare_client() -> OdooClient:
    """Get Odoo client with healthcare module support."""
    return get_client()


# === PATIENT MANAGEMENT ===

@app.tool()
async def create_patient(
    name: str,
    phone: str,
    email: str,
    date_of_birth: str,
    blood_type: str = "unknown",
    allergies: str = "",
    chronic_conditions: str = "",
    pregnancy_status: str = "not_applicable",
    risk_category: str = "low",
    insurance_provider: str = "",
    insurance_policy_number: str = ""
) -> str:
    """Create a new patient record in Odoo.

    Args:
        name: Patient full name
        phone: Patient phone number
        email: Patient email address
        date_of_birth: Date of birth (YYYY-MM-DD format)
        blood_type: Blood type (A+, A-, B+, B-, AB+, AB-, O+, O-, unknown)
        allergies: Known allergies
        chronic_conditions: Chronic medical conditions
        pregnancy_status: Pregnancy status (not_applicable, not_pregnant, pregnant, high_risk)
        risk_category: Risk category (low, medium, high)
        insurance_provider: Health insurance company
        insurance_policy_number: Insurance policy number

    Returns:
        Patient ID, Medical Record Number, and details
    """
    log_action("odoo_patient_created_requested", {
        "name": name,
        "blood_type": blood_type,
        "risk_category": risk_category,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return (
            f"[DRY RUN] Would create patient:\n"
            f"- Name: {name}\n"
            f"- Phone: {phone}\n"
            f"- Email: {email}\n"
            f"- DOB: {date_of_birth}\n"
            f"- Blood Type: {blood_type}\n"
            f"- Risk: {risk_category}"
        )

    try:
        client = get_healthcare_client()
        await client.authenticate()

        # Check if patient with email already exists
        existing = await client.search_read(
            "res.partner",
            [("email", "=", email), ("is_patient", "=", True)],
            ["id"],
            limit=1
        )

        if existing:
            return f"Patient with email {email} already exists (ID: {existing[0]['id']})"

        # Create patient
        patient_vals = {
            "name": name,
            "phone": phone,
            "email": email,
            "is_patient": True,
            "date_of_birth": date_of_birth,
            "blood_type": blood_type,
            "allergies": allergies,
            "chronic_conditions": chronic_conditions,
            "pregnancy_status": pregnancy_status,
            "risk_category": risk_category,
            "insurance_provider": insurance_provider,
            "insurance_policy_number": insurance_policy_number,
        }

        patient_id = await client.create("res.partner", patient_vals)

        # Read created patient to get MRN
        patients = await client.read("res.partner", [patient_id],
                                     ["id", "name", "medical_record_number"])
        patient = patients[0]

        log_action("odoo_patient_created", {
            "patient_id": patient_id,
            "medical_record_number": patient.get("medical_record_number"),
            "name": name
        })

        return (
            f"Patient created successfully:\n"
            f"- Patient ID: {patient_id}\n"
            f"- Medical Record #: {patient.get('medical_record_number')}\n"
            f"- Name: {patient.get('name')}\n"
            f"- Phone: {phone}\n"
            f"- Email: {email}\n"
            f"- Blood Type: {blood_type}\n"
            f"- Risk Category: {risk_category}"
        )

    except Exception as e:
        log_action("odoo_patient_create_error", {"error": str(e)})
        return f"Error creating patient: {str(e)}"


@app.tool()
async def get_patient(patient_id: int) -> str:
    """Retrieve complete patient profile including medical history.

    Args:
        patient_id: Patient record ID

    Returns:
        Complete patient profile with medical information
    """
    log_action("odoo_patient_get_requested", {
        "patient_id": patient_id,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would retrieve patient ID: {patient_id}"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        patients = await client.read("res.partner", [patient_id], [
            "id", "name", "medical_record_number", "is_patient",
            "date_of_birth", "age", "blood_type",
            "allergies", "chronic_conditions", "past_surgeries", "family_history",
            "pregnancy_status", "last_prenatal_checkup", "expected_due_date",
            "risk_category",
            "emergency_contact_id", "emergency_contact_phone",
            "primary_physician_id",
            "insurance_provider", "insurance_policy_number", "insurance_member_id",
            "phone", "email",
            "last_visit_date", "next_appointment", "total_visits"
        ])

        if not patients:
            return f"Patient not found with ID: {patient_id}"

        patient = patients[0]

        if not patient.get("is_patient"):
            return f"Record ID {patient_id} is not marked as a patient"

        # Format response
        result = f"""Patient Profile: {patient.get('name')}
{'=' * 50}
Medical Record #: {patient.get('medical_record_number', 'N/A')}

=== Basic Information ===
Name: {patient.get('name')}
Date of Birth: {patient.get('date_of_birth', 'N/A')}
Age: {patient.get('age', 'N/A')}
Blood Type: {patient.get('blood_type', 'Unknown')}
Risk Category: {patient.get('risk_category', 'low').upper()}

=== Medical History ===
Allergies: {patient.get('allergies', 'None reported')}
Chronic Conditions: {patient.get('chronic_conditions', 'None reported')}
Past Surgeries: {patient.get('past_surgeries', 'None reported')}
Family History: {patient.get('family_history', 'None reported')}

=== Women's Health ===
Pregnancy Status: {patient.get('pregnancy_status', 'not_applicable').replace('_', ' ').title()}
Expected Due Date: {patient.get('expected_due_date', 'N/A')}

=== Contact Information ===
Phone: {patient.get('phone', 'N/A')}
Email: {patient.get('email', 'N/A')}
Emergency Contact: {patient.get('emergency_contact_phone', 'N/A')}

=== Insurance ===
Provider: {patient.get('insurance_provider', 'N/A')}
Policy #: {patient.get('insurance_policy_number', 'N/A')}
Member ID: {patient.get('insurance_member_id', 'N/A')}

=== Visit History ===
Primary Physician: {patient.get('primary_physician_id', ['N/A'])[0] if isinstance(patient.get('primary_physician_id'), list) else 'N/A'}
Last Visit: {patient.get('last_visit_date', 'N/A')}
Next Appointment: {patient.get('next_appointment', 'N/A')}
Total Visits: {patient.get('total_visits', 0)}
"""

        log_action("odoo_patient_retrieved", {"patient_id": patient_id})
        return result

    except Exception as e:
        log_action("odoo_patient_get_error", {"error": str(e)})
        return f"Error retrieving patient: {str(e)}"


@app.tool()
async def search_patients(query: str, limit: int = 20) -> str:
    """Search patients by name, phone, email, or medical record number.

    Args:
        query: Search term (name, phone, email, or MRN)
        limit: Maximum results to return

    Returns:
        List of matching patients
    """
    log_action("odoo_patient_search_requested", {
        "query": query,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would search patients for: {query}"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        # Search in multiple fields
        patients = await client.search_read(
            "res.partner",
            [
                ("is_patient", "=", True),
                "|",
                "|",
                "|",
                ("name", "ilike", query),
                ("phone", "ilike", query),
                ("email", "ilike", query),
                ("medical_record_number", "ilike", query)
            ],
            ["id", "name", "medical_record_number", "phone", "email", "blood_type", "risk_category"],
            limit=limit,
            order="name asc"
        )

        if not patients:
            return f"No patients found matching: {query}"

        result = f"Found {len(patients)} patient(s):\n\n"
        for p in patients:
            result += f"- {p.get('name')} ({p.get('medical_record_number', 'No MRN')})\n"
            result += f"  ID: {p['id']}\n"
            result += f"  Phone: {p.get('phone', 'N/A')}\n"
            result += f"  Blood Type: {p.get('blood_type', 'Unknown')}\n"
            result += f"  Risk: {p.get('risk_category', 'low').upper()}\n\n"

        log_action("odoo_patient_search_completed", {"count": len(patients)})
        return result

    except Exception as e:
        log_action("odoo_patient_search_error", {"error": str(e)})
        return f"Error searching patients: {str(e)}"


@app.tool()
async def update_patient_vitals(
    patient_id: int,
    temperature: Optional[float] = None,
    blood_pressure_systolic: Optional[int] = None,
    blood_pressure_diastolic: Optional[int] = None,
    heart_rate: Optional[int] = None,
    respiratory_rate: Optional[int] = None,
    oxygen_saturation: Optional[int] = None,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    notes: Optional[str] = None
) -> str:
    """Record patient vitals from a visit.

    Args:
        patient_id: Patient record ID
        temperature: Body temperature in Celsius
        blood_pressure_systolic: Systolic BP (mmHg)
        blood_pressure_diastolic: Diastolic BP (mmHg)
        heart_rate: Heart rate (bpm)
        respiratory_rate: Respiratory rate (/min)
        oxygen_saturation: O2 saturation (%)
        weight: Weight in kg
        height: Height in cm
        notes: Additional notes

    Returns:
        Vitals record ID and summary
    """
    log_action("odoo_vitals_record_requested", {
        "patient_id": patient_id,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would record vitals for patient {patient_id}"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        # Verify patient exists
        patients = await client.read("res.partner", [patient_id], ["is_patient", "name"])
        if not patients or not patients[0].get("is_patient"):
            return f"Patient not found with ID: {patient_id}"

        patient_name = patients[0].get("name")

        # Create vitals record
        vitals_vals = {
            "patient_id": patient_id,
            "date_taken": datetime.now().isoformat(),
        }

        # Add provided vitals
        if temperature is not None:
            vitals_vals["temperature"] = temperature
        if blood_pressure_systolic is not None:
            vitals_vals["blood_pressure_systolic"] = blood_pressure_systolic
        if blood_pressure_diastolic is not None:
            vitals_vals["blood_pressure_diastolic"] = blood_pressure_diastolic
        if heart_rate is not None:
            vitals_vals["heart_rate"] = heart_rate
        if respiratory_rate is not None:
            vitals_vals["respiratory_rate"] = respiratory_rate
        if oxygen_saturation is not None:
            vitals_vals["oxygen_saturation"] = oxygen_saturation
        if weight is not None:
            vitals_vals["weight"] = weight
        if height is not None:
            vitals_vals["height"] = height
        if notes:
            vitals_vals["notes"] = notes

        vitals_id = await client.create("medical.vitals", vitals_vals)

        # Read created vitals
        vitals = await client.read("medical.vitals", [vitals_id],
                                  ["id", "date_taken", "temperature", "weight", "bmi"])
        vitals_data = vitals[0]

        log_action("odoo_vitals_recorded", {
            "vitals_id": vitals_id,
            "patient_id": patient_id
        })

        return (
            f"Vitals recorded successfully:\n"
            f"- Patient: {patient_name}\n"
            f"- Vitals ID: {vitals_id}\n"
            f"- Date: {vitals_data.get('date_taken')}\n"
            f"- Temperature: {temperature or 'N/A'}°C\n"
            f"- BP: {blood_pressure_systolic or 'N/A'}/{blood_pressure_diastolic or 'N/A'} mmHg\n"
            f"- Heart Rate: {heart_rate or 'N/A'} bpm\n"
            f"- Weight: {weight or 'N/A'} kg\n"
            f"- BMI: {vitals_data.get('bmi', 'N/A')}"
        )

    except Exception as e:
        log_action("odoo_vitals_error", {"error": str(e)})
        return f"Error recording vitals: {str(e)}"


# === APPOINTMENT MANAGEMENT ===

@app.tool()
async def create_appointment(
    patient_id: int,
    doctor_id: int,
    appointment_date: str,
    appointment_type: str = "consultation",
    duration: int = 30,
    notes: str = ""
) -> str:
    """Schedule a new appointment.

    Args:
        patient_id: Patient record ID
        doctor_id: Doctor record ID
        appointment_date: Date and time (YYYY-MM-DD HH:MM:SS format)
        appointment_type: Type (consultation, followup, checkup, emergency, prenatal, lab_test)
        duration: Duration in minutes
        notes: Additional notes

    Returns:
        Appointment ID and details
    """
    log_action("odoo_appointment_create_requested", {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create appointment for patient {patient_id} with doctor {doctor_id}"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        # Verify patient and doctor exist
        patients = await client.read("res.partner", [patient_id], ["is_patient", "name"])
        if not patients or not patients[0].get("is_patient"):
            return f"Patient not found with ID: {patient_id}"

        doctors = await client.read("res.partner", [doctor_id], ["is_doctor", "name"])
        if not doctors or not doctors[0].get("is_doctor"):
            return f"Doctor not found with ID: {doctor_id}"

        patient_name = patients[0].get("name")
        doctor_name = doctors[0].get("name")

        # Create appointment
        appointment_vals = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": appointment_date,
            "appointment_type": appointment_type,
            "duration": duration,
            "status": "scheduled",
        }

        if notes:
            appointment_vals["notes"] = notes

        appointment_id = await client.create("medical.appointment", appointment_vals)

        # Read created appointment
        appointments = await client.read("medical.appointment", [appointment_id],
                                      ["id", "name", "appointment_date", "status"])
        appointment = appointments[0]

        log_action("odoo_appointment_created", {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id
        })

        return (
            f"Appointment created successfully:\n"
            f"- Appointment ID: {appointment_id}\n"
            f"- Patient: {patient_name}\n"
            f"- Doctor: {doctor_name}\n"
            f"- Date/Time: {appointment.get('appointment_date')}\n"
            f"- Type: {appointment_type}\n"
            f"- Duration: {duration} minutes\n"
            f"- Status: {appointment.get('status')}"
        )

    except Exception as e:
        log_action("odoo_appointment_create_error", {"error": str(e)})
        return f"Error creating appointment: {str(e)}"


@app.tool()
async def get_upcoming_appointments(days: int = 7) -> str:
    """Get list of upcoming appointments in the next N days.

    Args:
        days: Number of days ahead to look

    Returns:
        List of upcoming appointments
    """
    log_action("odoo_appointments_upcoming_requested", {
        "days": days,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would get upcoming appointments for next {days} days"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        cutoff = (datetime.now() + timedelta(days=days)).isoformat()
        now = datetime.now().isoformat()

        appointments = await client.search_read(
            "medical.appointment",
            [
                ("status", "in", ["scheduled", "confirmed"]),
                ("appointment_date", ">=", now),
                ("appointment_date", "<=", cutoff)
            ],
            ["id", "name", "patient_id", "doctor_id", "appointment_date",
             "appointment_type", "status", "reminder_sent"],
            limit=100,
            order="appointment_date asc"
        )

        if not appointments:
            return f"No upcoming appointments in the next {days} days"

        result = f"Upcoming Appointments (next {days} days):\n\n"
        for apt in appointments:
            patient = apt.get("patient_id", [0, "Unknown"])
            patient_name = patient[1] if isinstance(patient, list) else "Unknown"

            doctor = apt.get("doctor_id", [0, "Unknown"])
            doctor_name = doctor[1] if isinstance(doctor, list) else "Unknown"

            reminder_status = "✓ Sent" if apt.get("reminder_sent") else "✗ Not sent"

            result += f"- {apt.get('name')}\n"
            result += f"  ID: {apt['id']}\n"
            result += f"  Date: {apt.get('appointment_date')}\n"
            result += f"  Patient: {patient_name}\n"
            result += f"  Doctor: {doctor_name}\n"
            result += f"  Type: {apt.get('appointment_type')}\n"
            result += f"  Status: {apt.get('status')}\n"
            result += f"  Reminder: {reminder_status}\n\n"

        log_action("odoo_appointments_upcoming_retrieved", {"count": len(appointments)})
        return result

    except Exception as e:
        log_action("odoo_appointments_upcoming_error", {"error": str(e)})
        return f"Error getting upcoming appointments: {str(e)}"


@app.tool()
async def update_appointment_status(
    appointment_id: int,
    status: str
) -> str:
    """Update appointment status.

    Args:
        appointment_id: Appointment record ID
        status: New status (scheduled, confirmed, in_progress, completed, cancelled, no_show)

    Returns:
        Confirmation message
    """
    log_action("odoo_appointment_status_update_requested", {
        "appointment_id": appointment_id,
        "status": status,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would update appointment {appointment_id} to status: {status}"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        await client.write("medical.appointment", [appointment_id], {"status": status})

        log_action("odoo_appointment_status_updated", {
            "appointment_id": appointment_id,
            "status": status
        })

        return f"Appointment {appointment_id} status updated to: {status}"

    except Exception as e:
        log_action("odoo_appointment_status_error", {"error": str(e)})
        return f"Error updating appointment status: {str(e)}"


@app.tool()
async def mark_appointment_reminder_sent(
    appointment_id: int,
    method: str = "whatsapp"
) -> str:
    """Mark that appointment reminder has been sent.

    Args:
        appointment_id: Appointment record ID
        method: Method used (whatsapp, email, sms, phone)

    Returns:
        Confirmation message
    """
    log_action("odoo_appointment_reminder_marked_requested", {
        "appointment_id": appointment_id,
        "method": method,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would mark reminder sent for appointment {appointment_id}"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        await client.write("medical.appointment", [appointment_id], {
            "reminder_sent": True,
            "reminder_method": method,
            "reminder_sent_date": datetime.now().isoformat()
        })

        log_action("odoo_appointment_reminder_marked", {
            "appointment_id": appointment_id,
            "method": method
        })

        return f"Reminder marked as sent for appointment {appointment_id} via {method}"

    except Exception as e:
        log_action("odoo_appointment_reminder_error", {"error": str(e)})
        return f"Error marking reminder: {str(e)}"


# === BILLING ===

@app.tool()
async def create_patient_invoice(
    patient_id: int,
    items: list,
    date: Optional[str] = None
) -> str:
    """Generate an invoice for patient services.

    Args:
        patient_id: Patient record ID
        items: List of invoice items [{"description": "...", "amount": 100.0, "quantity": 1}]
        date: Invoice date (YYYY-MM-DD, defaults to today)

    Returns:
        Invoice ID and details
    """
    log_action("odoo_patient_invoice_requested", {
        "patient_id": patient_id,
        "items_count": len(items),
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would create invoice for patient {patient_id} (requires approval)"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        # Verify patient exists
        patients = await client.read("res.partner", [patient_id],
                                     ["is_patient", "name"])
        if not patients or not patients[0].get("is_patient"):
            return f"Patient not found with ID: {patient_id}"

        patient_name = patients[0].get("name")

        # Build invoice lines
        invoice_lines = []
        for item in items:
            invoice_lines.append((0, 0, {
                "name": item.get("description", "Service"),
                "quantity": item.get("quantity", 1),
                "price_unit": item.get("amount", 0)
            }))

        invoice_vals = {
            "partner_id": patient_id,
            "patient_id": patient_id,
            "move_type": "out_invoice",
            "invoice_date": date or datetime.now().strftime('%Y-%m-%d'),
            "invoice_line_ids": invoice_lines
        }

        invoice_id = await client.create("account.move", invoice_vals)

        # Read created invoice
        invoices = await client.read("account.move", [invoice_id],
                                   ["id", "name", "amount_total", "state"])
        invoice = invoices[0]

        log_action("odoo_patient_invoice_created", {
            "invoice_id": invoice_id,
            "patient_id": patient_id,
            "amount": invoice.get("amount_total")
        })

        return (
            f"Patient invoice created:\n"
            f"- Invoice #: {invoice.get('name')}\n"
            f"- Invoice ID: {invoice_id}\n"
            f"- Patient: {patient_name}\n"
            f"- Total: ${invoice.get('amount_total', 0):.2f}\n"
            f"- Status: {invoice.get('state', 'draft')}\n"
            f"\nNote: This invoice requires approval before sending."
        )

    except Exception as e:
        log_action("odoo_patient_invoice_error", {"error": str(e)})
        return f"Error creating patient invoice: {str(e)}"


@app.tool()
async def get_patient_invoices(patient_id: int) -> str:
    """Get all invoices for a specific patient.

    Args:
        patient_id: Patient record ID

    Returns:
        List of patient invoices
    """
    log_action("odoo_patient_invoices_requested", {
        "patient_id": patient_id,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would get invoices for patient {patient_id}"

    try:
        client = get_healthcare_client()
        await client.authenticate()

        invoices = await client.search_read(
            "account.move",
            [
                ("partner_id", "=", patient_id),
                ("move_type", "=", "out_invoice")
            ],
            ["id", "name", "invoice_date", "amount_total", "state", "payment_state"],
            limit=50,
            order="invoice_date desc"
        )

        if not invoices:
            return f"No invoices found for patient ID: {patient_id}"

        result = f"Invoices for Patient {patient_id}:\n\n"
        total_outstanding = 0

        for inv in invoices:
            amount = inv.get("amount_total", 0)
            payment_state = inv.get("payment_state", "not_paid")
            if payment_state != "paid":
                total_outstanding += amount

            result += f"- Invoice: {inv.get('name', 'Draft')}\n"
            result += f"  ID: {inv['id']}\n"
            result += f"  Date: {inv.get('invoice_date', 'N/A')}\n"
            result += f"  Amount: ${amount:.2f}\n"
            result += f"  Status: {inv.get('state', 'draft')}\n"
            result += f"  Payment: {payment_state}\n\n"

        result += f"\nTotal Outstanding: ${total_outstanding:.2f}"

        log_action("odoo_patient_invoices_retrieved", {
            "patient_id": patient_id,
            "count": len(invoices)
        })
        return result

    except Exception as e:
        log_action("odoo_patient_invoices_error", {"error": str(e)})
        return f"Error retrieving patient invoices: {str(e)}"
