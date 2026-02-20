# Healthcare Automation - Manual Testing Guide

This guide walks through testing the entire healthcare automation flow manually.

---

## Prerequisites

1. **Backend server running:**
   ```bash
   cd backend
   uv run python main.py
   ```

2. **Required environment variables in `backend/.env`:**
   ```bash
   # Core
   VAULT_PATH=../AI_Employee_Vault
   API_PORT=8000
   DRY_RUN=false  # Set to false for real WhatsApp sends

   # Odoo (for EHR integration)
   ODOO_URL=http://localhost:8069
   ODOO_DB=odoo
   ODOO_USERNAME=admin
   ODOO_PASSWORD=admin

   # WhatsApp (for confirmations/reminders)
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   WHATSAPP_ACCESS_TOKEN=your_access_token

   # Auto-Approval
   AUTO_CONFIRM_APPOINTMENTS=true
   AUTO_ONBOARD_PATIENTENTS=true
   AUTO_REMINDERS_ENABLED=true
   ```

---

## Test 1: Automated Appointment Confirmation

### Step 1: Create a Test Patient

```bash
curl -X POST http://localhost:8000/api/healthcare/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Patient Auto",
    "phone": "+1234567890",
    "email": "testauto@example.com",
    "date_of_birth": "1990-01-01",
    "blood_type": "O+",
    "allergies": "None",
    "chronic_conditions": "",
    "pregnancy_status": "not_applicable",
    "risk_category": "low"
  }'
```

**Expected:** Returns patient ID
```json
{
  "id": 123,
  "name": "Test Patient Auto",
  "medical_record_number": "MRN001"
}
```

### Step 2: Create an Appointment (Should Auto-Send Confirmation)

```bash
curl -X POST http://localhost:8000/api/healthcare/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 123,
    "doctor_id": 2,
    "appointment_date": "2026-02-19 14:00:00",
    "appointment_type": "consultation",
    "duration": 30,
    "notes": "Test auto-confirmation"
  }'
```

**Expected:**
```json
{
  "id": 456,
  "confirmation_sent": true,
  "confirmation_status": {
    "auto_approved": true,
    "channel": "whatsapp",
    "success": true
  }
}
```

### Step 3: Verify WhatsApp Message

Check the phone (+1234567890) for a WhatsApp message like:
```
🩺 *Appointment Confirmed*

Dear Test Patient Auto,

Your appointment has been scheduled:

📅 *Date:* 2026-02-19
⏰ *Time:* 02:00 PM
👨‍⚕️ *Doctor:* OdooBot
📍 *Location:* Main Clinic
```

### Step 4: Check Audit Log

```bash
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep -A5 "auto_action"
```

**Expected:** Log entry with `"auto_approved": true`

---

## Test 2: 24h and 2h Automated Reminders

### Step 1: Create Appointment for Tomorrow

```bash
# Calculate tomorrow's date
TOMORROW=$(date -d "tomorrow 14:00" +%Y-%m-%d" "%H:%M:%S")

curl -X POST http://localhost:8000/api/healthcare/appointments \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": 123,
    \"doctor_id\": 2,
    \"appointment_date\": \"${TOMORROW}\",
    \"appointment_type\": \"consultation\",
    \"duration\": 30
  }"
```

### Step 2: Run Reminder Scheduler Watcher

```bash
# Terminal 1: Start reminder watcher
cd /home/madeeha/Documents/Personal-AI-Employee
uv run python watchers/reminder_scheduler_watcher.py
```

### Step 3: Check for Due Reminders

```bash
# Check 24h reminders
curl "http://localhost:8000/api/healthcare/appointments/upcoming/reminder-due?hours=24"

# Check 2h reminders
curl "http://localhost:8000/api/healthcare/appointments/upcoming/reminder-due?hours=2"
```

### Step 4: Verify Reminder was Sent

Check `AI_Employee_Vault/data/sent_reminders.json`:
```bash
cat AI_Employee_Vault/data/sent_reminders.json | python3 -m json.tool
```

**Expected:**
```json
{
  "reminders": [
    {
      "appointment_id": 456,
      "hours_before": 24,
      "channel": "whatsapp",
      "success": true,
      "sent_at": "2026-02-18T14:00:00"
    }
  ]
}
```

---

## Test 3: Patient Auto-Onboarding

### Step 1: Ensure Onboarding Watcher is Running

```bash
# Terminal 2: Start onboarding watcher
cd /home/madeeha/Documents/Personal-AI-Employee
uv run python watchers/patient_onboarding_watcher.py
```

### Step 2: Send WhatsApp from New Number

1. Send a WhatsApp message from a NEW phone number (not in Odoo)
2. Send any message like: "Hello, I need an appointment"

### Step 3: Check for New Patient in Odoo

```bash
# Search for patient by phone
curl "http://localhost:8000/api/healthcare/patients?phone=NEW_PHONE_NUMBER"
```

**Expected:** New patient created with name like "New Patient (+1234)"

### Step 4: Verify Welcome Message Sent

Check WhatsApp for welcome message:
```
🏥 *Welcome to Our Clinic!*

Thank you for reaching out. You've been registered in our healthcare system.
...
```

---

## Test 4: Odoo Appointment Watcher (Real-Time Monitoring)

### Step 1: Start Odoo Appointment Watcher

```bash
# Terminal 3: Start Odoo watcher
cd /home/madeeha/Documents/Personal-AI-Employee
uv run python watchers/odoo_appointment_watcher.py
```

### Step 2: Create Appointment Directly in Odoo

1. Open Odoo EHR: http://localhost:8069
2. Go to Healthcare → Appointments
3. Create new appointment
4. Save (do NOT send confirmation manually)

### Step 3: Wait 60 Seconds

The watcher polls every 60 seconds.

### Step 4: Verify Auto-Confirmation Sent

- Patient receives WhatsApp confirmation
- Check `AI_Employee_Vault/data/processed_appointments.json`

---

## Test 5: End-to-End Patient Journey

### Complete Flow:

1. **New patient messages on WhatsApp**
   - → Auto-onboarding creates patient record
   - → Welcome message sent

2. **Patient books appointment**
   - → Appointment created in Odoo
   - → Auto-confirmation sent via WhatsApp

3. **24 hours before appointment**
   - → Reminder watcher detects
   - → 24h reminder sent via WhatsApp

4. **2 hours before appointment**
   - → Reminder watcher detects
   - → 2h reminder sent via WhatsApp

5. **After appointment**
   - → Mark as done
   - → Invoice generated (requires approval)

---

## Test 6: Dry Run Mode (Safe Testing)

Set `DRY_RUN=true` in `.env` and verify:

1. **No actual messages sent**
2. **All actions logged to audit trail**
3. **Confirmations created with `"dry_run": true`**

```bash
# Check all dry run actions
grep "dry_run" AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

---

## Verification Commands

### Check System Status
```bash
curl http://localhost:8000/api/status
```

### Check Upcoming Appointments
```bash
curl "http://localhost:8000/api/healthcare/appointments/upcoming?days=7" | python3 -m json.tool
```

### Check Healthcare Stats
```bash
curl http://localhost:8000/api/healthcare/stats | python3 -m json.tool
```

### Check Reminder Status for Appointment
```bash
curl http://localhost:8000/api/healthcare/appointments/456/reminder-status | python3 -m json.tool
```

### View Sent Confirmations
```bash
grep "appointment_confirmation" AI_Employee_Vault/Logs/*.json
```

### View Sent Reminders
```bash
cat AI_Employee_Vault/data/sent_reminders.json | python3 -m json.tool
```

---

## Troubleshooting

### No WhatsApp Messages Received

1. **Check credentials:**
   ```bash
   echo $WHATSAPP_PHONE_NUMBER_ID
   echo $WHATSAPP_ACCESS_TOKEN
   ```

2. **Check DRY_RUN mode:**
   ```bash
   grep DRY_RUN backend/.env
   ```

3. **Check logs:**
   ```bash
   tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
   ```

### Watchers Not Running

1. **Check PM2 status:**
   ```bash
   pm2 status
   pm2 logs odoo-appointment-watcher
   ```

2. **Check if enabled in env:**
   ```bash
   grep ODOO_APPOINTMENT_WATCHER_ENABLED backend/.env
   grep AUTO_REMINDERS_ENABLED backend/.env
   ```

### Odoo Connection Issues

1. **Test Odoo connection:**
   ```bash
   curl http://localhost:8069/jsonrpc
   ```

2. **Check Odoo credentials in `.env`**

---

## Quick Test Script

Save as `quick_test.sh`:

```bash
#!/bin/bash

API="http://localhost:8000"

echo "=== Healthcare Automation Quick Test ==="

echo -e "\n[1] Creating test patient..."
PATIENT=$(curl -s -X POST $API/api/healthcare/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quick Test",
    "phone": "+9999999999",
    "email": "quicktest@example.com",
    "date_of_birth": "1990-01-01"
  }')

echo $PATIENT | python3 -m json.tool
PATIENT_ID=$(echo $PATIENT | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo -e "\n[2] Creating appointment..."
APPOINTMENT=$(curl -s -X POST $API/api/healthcare/appointments \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": $PATIENT_ID,
    \"doctor_id\": 2,
    \"appointment_date\": \"2026-02-19 15:00:00\"
  }")

echo $APPOINTMENT | python3 -m json.tool

echo -e "\n[3] Checking upcoming appointments..."
curl -s "$API/api/healthcare/appointments/upcoming?days=7" | python3 -m json.tool | head -20

echo -e "\n[4] Checking audit log..."
grep "auto_action" AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | tail -5

echo -e "\n=== Test Complete ==="
```

Run:
```bash
chmod +x quick_test.sh
./quick_test.sh
```
