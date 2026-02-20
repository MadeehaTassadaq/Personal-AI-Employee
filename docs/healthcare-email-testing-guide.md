# Email Patient Intake Testing Guide

This guide provides step-by-step instructions for manually testing the email-based AI Healthcare integration.

## Prerequisites

- Backend server running: `cd backend && python main.py`
- Gmail API credentials configured (see `.env.example`)
- Environment variables configured (GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH)
- `DRY_RUN=true` for testing (set to `false` for actual sending)

## Test Scenarios

### Scenario 1: Email Emergency Detection (T065)

**Objective**: Verify that emergency emails are correctly identified and escalated.

#### Steps:

1. **Send Test Emergency Email**
   - From your email client, send an email to the clinic inbox
   - Subject: "Urgent - Chest Pain"
   - Body: "I'm experiencing severe chest pain and difficulty breathing. I need immediate help."

2. **Monitor Gmail Watcher**
   ```bash
   # Check logs for email receipt
   tail -f vault/Logs/$(date +%Y-%m-%d).json | grep "email_received"
   ```

3. **Verify AI Triage Results**
   ```bash
   # Check Pending_Approval folder
   ls -la vault/Pending_Approval/

   # View the generated draft
   cat vault/Pending_Approval/*.md
   ```

4. **Expected Results:**
   - [ ] Email received by gmail_watcher
   - [ ] Triage classification: urgency="emergency"
   - [ ] Escalation required: true
   - [ ] Approval required: true
   - [ ] Draft saved to Pending_Approval/
   - [ ] Draft includes emergency response template
   - [ ] Draft directs to emergency care (not medical advice)

#### Success Criteria:
- Emergency keywords trigger emergency classification
- Draft includes emergency contact information
- No medical advice is provided in the draft
- Human approval is required before any response

---

### Scenario 2: Email Routine Appointment (T066)

**Objective**: Verify routine appointment requests are handled efficiently.

#### Steps:

1. **Send Test Routine Email**
   - Subject: "Appointment Request"
   - Body: "Hi, I would like to schedule a routine checkup sometime next week. I'm flexible with dates."

2. **Monitor Processing**
   ```bash
   # Watch logs
   tail -f vault/Logs/$(date +%Y-%m-%d).json
   ```

3. **Check Draft Generation**
   ```bash
   # View draft in Pending_Approval
   cat vault/Pending_Approval/*.md | grep -A 20 "Appointment Booking"
   ```

4. **Verify Conversation Storage**
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'backend')
   from backend.services.orchestrator import get_orchestrator

   orch = get_orchestrator()
   ctx = orch.get_conversation_context(patient_identifier='test@example.com')
   print(f'Conversation ID: {ctx.get(\"conversation_id\")}')
   print(f'Last Intent: {ctx.get(\"last_intent\")}')
   print(f'Message Count: {ctx.get(\"message_count\")}')
   "
   ```

5. **Expected Results:**
   - [ ] Triage classification: urgency="routine"
   - [ ] Intent: "appointment_booking"
   - [ ] Confidence score >= 0.8
   - [ ] Draft includes appointment booking template
   - [ ] Draft asks for preferred date/time
   - [ ] Conversation context stored with email address

#### Success Criteria:
- Routine appointments are not escalated
- Email-specific formatting (Dear Patient, Best regards)
- Conversation context maintained across messages

---

### Scenario 3: Email Approval Workflow (T067)

**Objective**: Test the complete email approval workflow.

#### Steps:

1. **Create Test Draft**
   - Either send a real email (scenarios above)
   - Or manually create a draft in Pending_Approval/

2. **Review Draft**
   ```bash
   # List all drafts
   ls -la vault/Pending_Approval/

   # View draft content
   cat vault/Pending_Approval/*.md
   ```

3. **Approve Draft**
   - Edit draft if needed (optional)
   - Move to Approved/ folder
   ```bash
   mv vault/Pending_Approval/test-draft.md vault/Approved/
   ```

4. **Monitor Execution**
   ```bash
   # Monitor approval checker logs
   tail -f vault/Logs/$(date +%Y-%m-%d).json | grep "approval"
   ```

5. **Verify Sending**
   - In DRY_RUN mode: Check logs for "[DRY RUN] Would send email"
   - In live mode: Check email sent to recipient
   - File moved to Done/ with status:sent

6. **Check Done Folder**
   ```bash
   # Verify completion
   ls -la vault/Done/

   # View completion status
   cat vault/Done/*.md | grep "status:"
   ```

4. **Expected Results:**
   - [ ] Draft moved from Pending_Approval to Approved
   - [ ] Approval_checker processed the draft
   - [ ] Email sent (or logged in DRY_RUN mode)
   - [ ] File moved to Done/ with status:sent
   - [ ] Subject line appropriate (e.g., "Re: Your Message")

#### Success Criteria:
- Complete workflow executes without errors
- Email formatted correctly with greeting/closing
- Sent only after human approval
- Audit trail maintained in Done/ folder

---

### Scenario 4: Email Thread Context (Optional)

**Objective**: Verify conversation context is maintained across email threads.

#### Steps:

1. **Send First Email**
   - Subject: "Question about appointment"
   - Body: "What are your hours next week?"

2. **Wait for Processing**
   - Let AI triage process and generate draft
   - Move to Done/ (reject or respond)

3. **Send Follow-up Email**
   - Subject: "Re: Question about appointment"
   - Body: "Also, do I need to bring anything?"

4. **Verify Context Retention**
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'backend')
   from backend.services.orchestrator import get_orchestrator

   orch = get_orchestrator()
   history = orch.get_conversation_history('email_conv_001', limit=10)
   print(f'Messages in thread: {len(history)}')
   for msg in history:
       print(f'  [{msg[\"sender\"]}]: {msg[\"message_text\"][:40]}...')
   "
   ```

5. **Expected Results:**
   - [ ] Both emails stored in same conversation context
   - [ ] Thread history accessible
   - [ ] Context maintained across messages

---

### Scenario 5: Specialized Email Templates

**Objective**: Test various healthcare-specific email templates.

#### Prescription Refill Test:

1. **Send Prescription Refill Email**
   ```
   Subject: Prescription Refill Request
   Body: I need a refill for my blood pressure medication.
         The prescription is running out in 3 days.
   ```

2. **Verify Template:**
   - [ ] Intent: "prescription_refill"
   - [ ] Draft includes medication-specific template
   - [ ] Asks for pharmacy information
   - [ ] Notes 1-2 day processing time

#### Billing Question Test:

1. **Send Billing Inquiry**
   ```
   Subject: Question about my bill
   Body: I have a question about the invoice I received.
         The amount seems incorrect.
   ```

2. **Verify Template:**
   - [ ] Intent: "billing_question"
   - [ ] Draft includes billing-specific template
   - [ ] Asks for invoice/statement number
   - [ ] Includes billing hours information

---

## Quick Email Test Script

```bash
#!/bin/bash
# Quick email intake test

echo "Testing email AI triage..."

python3 -c "
import asyncio
import sys
sys.path.insert(0, 'backend')
sys.path.insert(0, '.')

from watchers.ai_integration import get_ai_integration

async def test_email():
    ai = get_ai_integration()

    # Test emergency email
    draft = await ai.triage_and_draft(
        message='I have severe chest pain and need help',
        channel='email',
        recipient='patient@example.com',
        sender_name='John Doe'
    )

    print(f'Emergency Test:')
    print(f'  Urgency: {draft.urgency}')
    print(f'  Intent: {draft.intent}')
    print(f'  Escalation: {draft.escalation_required}')
    print(f'  Approval: {draft.requires_approval}')
    print(f'  Reply preview: {draft.draft_reply[:100]}...')

asyncio.run(test_email())
"
```

---

## Troubleshooting

### Issue: "Gmail authentication failed"
**Solution:**
1. Check credentials path in `.env`
2. Run OAuth flow: `python watchers/gmail_watcher.py`
3. Verify token saved to `GMAIL_TOKEN_PATH`

### Issue: "No emails received"
**Solution:**
1. Check Gmail watcher is running
2. Verify credentials are valid
3. Check Gmail label filter (default: INBOX)
4. Ensure test email is unread

### Issue: "AI triage not triggering"
**Solution:**
1. Check `enable_ai_triage=True` in gmail_watcher
2. Verify ai_integration module is accessible
3. Check for import errors in logs

### Issue: "Email not sent after approval"
**Solution:**
1. Check DRY_RUN setting (must be false for actual sending)
2. Verify Gmail MCP server is accessible
3. Check approval_checker logs
4. Verify recipient email is valid

### Issue: "Conversation context not stored"
**Solution:**
1. Verify database path exists: `backend/data/conversations/`
2. Check orchestrator imports
3. Look for storage errors in logs
4. Test conversation storage independently

---

## Testing Checklist

Use this checklist to track your testing progress:

### Email Intake (Phase 4)
- [ ] Emergency detection via email (Scenario 1)
- [ ] Routine appointment via email (Scenario 2)
- [ ] Approval workflow (Scenario 3)
- [ ] Email thread context (Scenario 4, optional)
- [ ] Prescription refill template (Scenario 5)
- [ ] Billing question template (Scenario 5)
- [ ] Medical inquiry template (Scenario 5)

### Verification
- [ ] All emails properly triaged
- [ ] Drafts formatted correctly
- [ ] Conversation context maintained
- [ ] Approval workflow functional
- [ ] Emails sent after approval
- [ ] Audit trail complete

---

## Comparison: WhatsApp vs Email

| Feature | WhatsApp | Email |
|---------|----------|-------|
| Tone | Friendly, informal, emojis | Formal, structured |
| Greeting | Hi [Name] | Dear Patient, |
| Closing | (None or short) | Best regards, Clinic Team |
| Emergency | 📍 Location prompt | Full emergency instructions |
| Length | Short, concise | Detailed, comprehensive |
| Templates | Simpler | More specialized |

---

## Next Steps After Testing

1. **Review Logs**: Check `vault/Logs/` for any errors
2. **Clean Up Test Data**: Remove test conversations from database
3. **Document Findings**: Note any issues or improvements needed
4. **Prepare for Production**:
   - Set `DRY_RUN=false` for live email sending
   - Configure Gmail service account
   - Set up proper monitoring
5. **Test Live**: Send actual test emails to verify end-to-end flow

---

## Email-Specific Environment Variables

```bash
# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=./credentials/client_secrets.json
GMAIL_TOKEN_PATH=./credentials/gmail_token.json
GMAIL_LABEL=INBOX

# AI Integration
DRY_RUN=true  # Set to false for live sending
AUTO_APPROVE_SAFE=false

# Email Settings
CLINIC_EMAIL=noreply@clinic.example.com
CLINIC_PHONE=+1-555-123-4567
CLINIC_HOURS="Monday-Friday, 9:00 AM - 5:00 PM"
```

---

## Notes

- Email triage uses the same AI model as WhatsApp (gpt-4o)
- Conversation context is shared across channels (same patient = same context)
- Email threads are tracked by sender email address
- All healthcare templates comply with medical communication best practices
- Emergency responses direct to care, never provide medical advice
