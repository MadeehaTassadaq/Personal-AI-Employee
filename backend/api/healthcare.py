"""Healthcare API endpoints."""
import os
import sys
from datetime import datetime, date, timedelta
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/healthcare", tags=["healthcare"])

# Add MCP to path
mcp_path = Path(os.getcwd()) / "mcp_services/odoo_mcp"
if str(mcp_path) not in sys.path:
    sys.path.insert(0, str(mcp_path))

from mcp_services.odoo_mcp.jsonrpc_client import get_client


# === Request/Response Models ===

class PatientCreate(BaseModel):
    name: str
    phone: str
    email: str
    date_of_birth: str
    blood_type: str = "unknown"
    allergies: str = ""
    chronic_conditions: str = ""
    pregnancy_status: str = "not_applicable"
    risk_category: str = "low"


class PatientUpdate(BaseModel):
    date_of_birth: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    pregnancy_status: Optional[str] = None
    risk_category: Optional[str] = None
    primary_physician_id: Optional[int] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: str
    appointment_type: str = "consultation"
    duration: int = 30
    notes: str = ""


class VitalsCreate(BaseModel):
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    notes: str = ""


class InvoiceItem(BaseModel):
    description: str
    amount: float
    quantity: float = 1


class InvoiceCreate(BaseModel):
    items: list[InvoiceItem]
    date: Optional[str] = None


# === Helper Functions ===

async def get_odoo_client():
    """Get Odoo client from MCP server."""
    client = get_client()
    await client.authenticate()
    return client


def is_dry_run() -> bool:
    """Check if DRY_RUN mode is enabled."""
    return os.getenv("DRY_RUN", "true").lower() == "true"


# === Patient Endpoints ===

@router.get("/patients")
async def list_patients(search: Optional[str] = None):
    """List all patients with optional search."""
    try:
        client = await get_odoo_client()

        domain = [("is_patient", "=", True)]
        if search:
            domain.append(("name", "ilike", search))

        patients = await client.search_read(
            "res.partner",
            domain,
            ["id", "name", "medical_record_number", "phone", "email", "blood_type", "risk_category"],
            limit=100,
            order="name asc"
        )

        return {"patients": patients, "count": len(patients)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing patients: {str(e)}")


@router.get("/patients/{patient_id}")
async def get_patient(patient_id: int):
    """Get complete patient profile."""
    try:
        client = await get_odoo_client()

        patients = await client.read("res.partner", [patient_id], [
            "id", "name", "medical_record_number", "is_patient",
            "date_of_birth", "blood_type", "age",
            "allergies", "chronic_conditions", "past_surgeries", "family_history",
            "pregnancy_status", "risk_category",
            "primary_physician_id", "emergency_contact_phone",
            "insurance_provider", "insurance_policy_number",
            "phone", "email",
            "last_visit_date", "total_visits"
        ])

        if not patients:
            raise HTTPException(status_code=404, detail="Patient not found")

        patient = patients[0]
        if not patient.get("is_patient"):
            raise HTTPException(status_code=400, detail="Partner ID is not marked as patient")

        return patient
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving patient: {str(e)}")


@router.post("/patients")
async def create_patient(request: PatientCreate):
    """Create new patient profile."""
    if is_dry_run():
        return {"message": "DRY_RUN: Would create patient", "data": request.dict()}

    try:
        client = await get_odoo_client()

        # Check if email already exists
        existing = await client.search_read(
            "res.partner",
            [("email", "=", request.email), ("is_patient", "=", True)],
            ["id"],
            limit=1
        )

        if existing:
            raise HTTPException(status_code=400, detail="Patient with this email already exists")

        # Create patient
        patient_vals = {
            "name": request.name,
            "phone": request.phone,
            "email": request.email,
            "is_patient": True,
            "date_of_birth": request.date_of_birth,
            "blood_type": request.blood_type,
            "allergies": request.allergies,
            "chronic_conditions": request.chronic_conditions,
            "pregnancy_status": request.pregnancy_status,
            "risk_category": request.risk_category,
        }

        patient_id = await client.create("res.partner", patient_vals)

        # Read created patient
        patients = await client.read("res.partner", [patient_id],
                                     ["id", "name", "medical_record_number"])
        patient = patients[0]

        return {
            "id": patient["id"],
            "name": patient["name"],
            "medical_record_number": patient.get("medical_record_number")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating patient: {str(e)}")


@router.put("/patients/{patient_id}")
async def update_patient(patient_id: int, request: PatientUpdate):
    """Update patient information."""
    if is_dry_run():
        return {"message": "DRY_RUN: Would update patient", "data": request.dict()}

    try:
        client = await get_odoo_client()

        # Verify patient exists
        patients = await client.read("res.partner", [patient_id], ["is_patient"])
        if not patients or not patients[0].get("is_patient"):
            raise HTTPException(status_code=404, detail="Patient not found")

        # Build update values
        update_vals = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                update_vals[field] = value

        if update_vals:
            await client.write("res.partner", [patient_id], update_vals)

        return {"message": "Patient updated successfully", "id": patient_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating patient: {str(e)}")


# === Appointment Endpoints ===

@router.get("/appointments")
async def list_appointments(
    from_date: str = Query(..., description="From date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="To date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """List appointments in date range."""
    try:
        client = await get_odoo_client()

        domain = [
            ("appointment_date", ">=", from_date),
            ("appointment_date", "<=", to_date)
        ]

        if status:
            domain.append(("status", "=", status))

        appointments = await client.search_read(
            "medical.appointment",
            domain,
            ["id", "name", "patient_id", "doctor_id", "appointment_date", "appointment_type", "status"],
            limit=100,
            order="appointment_date asc"
        )

        return {"appointments": appointments, "count": len(appointments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing appointments: {str(e)}")


@router.post("/appointments")
async def create_appointment(request: AppointmentCreate):
    """Schedule new appointment."""
    if is_dry_run():
        return {"message": "DRY_RUN: Would create appointment", "data": request.dict()}

    try:
        client = await get_odoo_client()

        appointment_vals = {
            "patient_id": request.patient_id,
            "doctor_id": request.doctor_id,
            "appointment_date": request.appointment_date,
            "appointment_type": request.appointment_type,
            "duration": request.duration,
            "status": "scheduled",
        }

        if request.notes:
            appointment_vals["notes"] = request.notes

        appointment_id = await client.create("medical.appointment", appointment_vals)

        # Read created appointment
        appointments = await client.read("medical.appointment", [appointment_id],
                                      ["id", "name", "appointment_date"])
        appointment = appointments[0]

        return {
            "id": appointment["id"],
            "name": appointment["name"],
            "appointment_date": appointment.get("appointment_date")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating appointment: {str(e)}")


@router.get("/appointments/upcoming")
async def upcoming_appointments(days: int = Query(7, description="Days ahead to look")):
    """Get upcoming appointments for reminders."""
    try:
        client = await get_odoo_client()

        cutoff = (datetime.now() + timedelta(days=days)).isoformat()

        appointments = await client.search_read(
            "medical.appointment",
            [
                ("status", "in", ["scheduled", "confirmed"]),
                ("appointment_date", ">=", datetime.now().isoformat()),
                ("appointment_date", "<=", cutoff)
            ],
            ["id", "name", "patient_id", "doctor_id", "appointment_date", "status", "reminder_sent"],
            limit=100,
            order="appointment_date asc"
        )

        return {"appointments": appointments, "count": len(appointments)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting upcoming appointments: {str(e)}")


@router.put("/appointments/{appointment_id}/status")
async def update_appointment_status(appointment_id: int, status: str):
    """Update appointment status."""
    if is_dry_run():
        return {"message": "DRY_RUN: Would update appointment status"}

    try:
        client = await get_odoo_client()

        await client.write("medical.appointment", [appointment_id], {"status": status})

        return {"message": "Appointment status updated", "id": appointment_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating appointment: {str(e)}")


# === Medical Records ===

@router.get("/patients/{patient_id}/vitals")
async def get_patient_vitals(patient_id: int):
    """Get patient vitals history."""
    try:
        client = await get_odoo_client()

        vitals = await client.search_read(
            "medical.vitals",
            [("patient_id", "=", patient_id)],
            ["id", "date_taken", "temperature", "blood_pressure_systolic", "blood_pressure_diastolic",
             "heart_rate", "weight", "height", "notes"],
            limit=50,
            order="date_taken desc"
        )

        return {"vitals": vitals, "count": len(vitals)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving vitals: {str(e)}")


@router.post("/patients/{patient_id}/vitals")
async def record_vitals(patient_id: int, request: VitalsCreate):
    """Record new patient vitals."""
    if is_dry_run():
        return {"message": "DRY_RUN: Would record vitals", "data": request.dict()}

    try:
        client = await get_odoo_client()

        # Verify patient exists
        patients = await client.read("res.partner", [patient_id], ["is_patient"])
        if not patients or not patients[0].get("is_patient"):
            raise HTTPException(status_code=404, detail="Patient not found")

        vitals_vals = {
            "patient_id": patient_id,
            "date_taken": datetime.now().isoformat(),
        }

        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                vitals_vals[field] = value

        vitals_id = await client.create("medical.vitals", vitals_vals)

        return {"message": "Vitals recorded successfully", "id": vitals_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording vitals: {str(e)}")


# === Billing ===


@router.post("/whatsapp/send")
async def send_whatsapp_reminder(
    phone: str,
    message: str,
    appointment_id: Optional[int] = None
):
    """Send WhatsApp reminder for healthcare appointment.

    This endpoint is called by Odoo when sending appointment reminders.
    It uses the WhatsApp MCP server to send the message.

    Args:
        phone: Phone number to send reminder to
        message: Message content
        appointment_id: Optional appointment ID for tracking

    Returns:
        Response indicating success or failure
    """
    try:
        # Check if DRY_RUN is enabled
        dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        if dry_run:
            return {
                "success": True,
                "message": f"[DRY RUN] Would send WhatsApp to {phone}: {message[:50]}...",
                "sent_at": datetime.now().isoformat()
            }

        # Try to send via WhatsApp MCP
        try:
            # Import WhatsApp MCP function
            import sys
            from pathlib import Path
            mcp_path = Path(os.getcwd()) / "mcp_services/whatsapp_mcp"
            if str(mcp_path) not in sys.path:
                sys.path.insert(0, str(mcp_path))

            from mcp_services.whatsapp_mcp.server import send_message

            # Format phone number if needed
            phone_clean = phone.strip().replace(" ", "").replace("-", "")

            # Send the message
            result = await send_message(phone_clean, message)

            if result.get("success"):
                return {
                    "success": True,
                    "message": "WhatsApp reminder sent successfully",
                    "sent_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to send WhatsApp reminder",
                    "error": result.get("error", "Unknown error")
                }

        except ImportError:
            # If MCP is not available, log the action
            import logging
            logging.warning(f"WhatsApp MCP not available, logging reminder: {phone} - {message}")

            return {
                "success": True,
                "message": f"[MCP NOT AVAILABLE] Would send to {phone}: {message[:50]}...",
                "sent_at": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "success": False,
            "message": "Error sending WhatsApp reminder",
            "error": str(e)
        }


# === Billing ===

@router.post("/patients/{patient_id}/invoice")
async def create_patient_invoice(patient_id: int, request: InvoiceCreate):
    """Create invoice for patient services."""
    if is_dry_run():
        return {"message": "DRY_RUN: Would create invoice (requires approval)", "data": request.dict()}

    try:
        client = await get_odoo_client()

        # Verify patient exists
        patients = await client.read("res.partner", [patient_id], ["is_patient", "name"])
        if not patients or not patients[0].get("is_patient"):
            raise HTTPException(status_code=404, detail="Patient not found")

        # Build invoice lines
        invoice_lines = []
        for item in request.items:
            invoice_lines.append((0, 0, {
                "name": item.description,
                "quantity": item.quantity,
                "price_unit": item.amount
            }))

        invoice_vals = {
            "partner_id": patient_id,
            "patient_id": patient_id,
            "move_type": "out_invoice",
            "invoice_date": request.date or date.today().isoformat(),
            "invoice_line_ids": invoice_lines
        }

        invoice_id = await client.create("account.move", invoice_vals)

        # Read created invoice
        invoices = await client.read("account.move", [invoice_id],
                                   ["id", "name", "amount_total", "state"])
        invoice = invoices[0]

        return {
            "id": invoice["id"],
            "name": invoice["name"],
            "amount_total": invoice.get("amount_total"),
            "state": invoice.get("state")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {str(e)}")


@router.get("/patients/{patient_id}/invoices")
async def get_patient_invoices(patient_id: int):
    """Get all invoices for a specific patient."""
    try:
        client = await get_odoo_client()

        invoices = await client.search_read(
            "account.move",
            [
                ("patient_id", "=", patient_id),
                ("move_type", "=", "out_invoice")
            ],
            ["id", "name", "invoice_date", "amount_total", "state", "payment_state"],
            limit=50,
            order="invoice_date desc"
        )

        return {"invoices": invoices, "count": len(invoices)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving invoices: {str(e)}")


@router.get("/stats")
async def get_healthcare_stats():
    """Get healthcare summary statistics."""
    try:
        client = await get_odoo_client()

        # Get total patients
        patients = await client.search_read(
            "res.partner",
            [("is_patient", "=", True)],
            ["id"],
            limit=1
        )
        total_patients = len(patients)

        # Get high risk patients
        high_risk_patients = await client.search_read(
            "res.partner",
            [("is_patient", "=", True), ("risk_category", "=", "high")],
            ["id"],
            limit=1
        )

        # Get pregnant patients
        pregnant_patients = await client.search_read(
            "res.partner",
            [("is_patient", "=", True), ("pregnancy_status", "in", ["pregnant", "high_risk"])],
            ["id"],
            limit=1
        )

        # Get today's appointments
        today = date.today().isoformat()
        today_appointments = await client.search_read(
            "medical.appointment",
            [
                ("appointment_date", ">=", today),
                ("appointment_date", "<=", f"{today} 23:59:59"),
                ("status", "in", ["scheduled", "confirmed"])
            ],
            ["id"],
            limit=1
        )

        # Get upcoming appointments (next 7 days)
        upcoming_date = (datetime.now() + timedelta(days=7)).isoformat()
        upcoming_appointments = await client.search_read(
            "medical.appointment",
            [
                ("appointment_date", ">=", today),
                ("appointment_date", "<=", upcoming_date),
                ("status", "in", ["scheduled", "confirmed"])
            ],
            ["id"],
            limit=1
        )

        # Get pending invoices (draft or open)
        pending_invoices = await client.search_read(
            "account.move",
            [
                ("move_type", "=", "out_invoice"),
                ("state", "in", ["draft", "posted"])
            ],
            ["id"],
            limit=1
        )

        return {
            "total_patients": total_patients,
            "high_risk_patients": len(high_risk_patients),
            "pregnant_patients": len(pregnant_patients),
            "today_appointments": len(today_appointments),
            "upcoming_appointments": len(upcoming_appointments),
            "pending_invoices": len(pending_invoices),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving healthcare stats: {str(e)}")
