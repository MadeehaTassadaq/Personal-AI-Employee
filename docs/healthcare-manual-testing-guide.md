# Healthcare Integration Manual Testing Guide

This guide provides step-by-step instructions for manually testing the AI Healthcare integration scenarios.

## Prerequisites

- Backend server running: `cd backend && python main.py`
- Odoo EHR server running and accessible
- Environment variables configured (see `.env.example`)
- WhatsApp MCP service configured (or DRY_RUN=true)

## Test Scenarios

### Scenario 1: Emergency Detection (T056)

**Objective**: Verify that emergency messages are correctly identified and escalated.

#### Steps:

1. **Simulate Emergency Message**
   ```bash
   cd backend
   python -c "
   import asyncio
   import sys
   sys.path.insert(0, '..')

   from watchers.ai_integration import get_ai_integration

   async def test():
       ai = get_ai_integration()
       draft = await ai.triage_and_draft(
           message='I have severe chest pain and difficulty breathing',
           channel='whatsapp',
           recipient='+1234567890',
           sender_name='John Doe'
       )
       print(f'Urgency: {draft.urgency}')
       print(f'Escalation Required: {draft.escalation_required}')
       print(f'Approval Required: {draft.requires_approval}')

   asyncio.run(test())
   "
   ```

2. **Verify Results:**
   - [ ] Urgency is classified as "emergency"
   - [ ] Escalation required is True
   - [ ] Approval required is True
   - [ ] Draft is saved to `Pending_Approval/`
   - [ ] Draft includes escalation reason

3. **Check Vault:**
   ```bash
   ls -la vault/Pending_Approval/
   cat vault/Pending_Approval/*.md | grep -A 10 "Emergency"
   ```

4. **Expected Draft Reply:**
   - Directs patient to emergency care
   - Does NOT provide medical advice
   - Includes emergency contact information

#### Success Criteria:
- All emergency keywords trigger emergency classification
- Escalation is always required for emergencies
- Human approval is required before any response

---

### Scenario 2: Routine Appointment (T057)

**Objective**: Verify routine appointment requests are handled efficiently with appropriate automation.

#### Steps:

1. **Simulate Routine Message**
   ```bash
   cd backend
   python -c "
   import asyncio
   import sys
   sys.path.insert(0, '..')

   from watchers.ai_integration import get_ai_integration

   async def test():
       ai = get_ai_integration()
       draft = await ai.triage_and_draft(
           message='I would like to schedule a routine checkup next week',
           channel='whatsapp',
           recipient='+1234567890',
           sender_name='Jane Smith'
       )
       print(f'Urgency: {draft.urgency}')
       print(f'Intent: {draft.intent}')
       print(f'Confidence: {draft.triage_confidence}')
       print(f'Approval Required: {draft.requires_approval}')

   asyncio.run(test())
   "
   ```

2. **Verify Results:**
   - [ ] Urgency is classified as "routine"
   - [ ] Intent is "appointment_booking"
   - [ ] Confidence score is >= 0.8
   - [ ] Draft includes helpful response

3. **Check Conversation Storage:**
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'backend')
   from backend.services.orchestrator import get_orchestrator

   orch = get_orchestrator()
   ctx = orch.get_conversation_context(patient_identifier='+1234567890')
   print(ctx)
   "
   ```

4. **Expected Behavior:**
   - Message classified correctly
   - Conversation context stored
   - Appropriate response drafted

#### Success Criteria:
- Routine messages are not escalated
- Conversation context is maintained
- Draft replies are helpful and appropriate

---

### Scenario 3: New Patient Onboarding (T058)

**Objective**: Verify new patients are properly onboarded and registered in Odoo.

#### Steps:

1. **Simulate New Patient Message**
   ```bash
   cd backend
   python -c "
   import asyncio
   import sys
   sys.path.insert(0, '..')

   from watchers.ai_integration import get_ai_integration

   async def test():
       ai = get_ai_integration()
       draft = await ai.triage_and_draft(
           message='Hi, I\\'m a new patient. How do I register and book an appointment?',
           channel='whatsapp',
           recipient='+19998887777',
           sender_name='New Patient'
       )
       print(f'Intent: {draft.intent}')
       print(f'Task Created: {draft.metadata.get(\"task_created\")}')
       print(f'Draft Reply: {draft.draft_reply[:100]}...')

   asyncio.run(test())
   "
   ```

2. **Verify Results:**
   - [ ] Intent is correctly identified
   - [ ] Task is created for patient onboarding
   - [ ] Draft includes registration instructions
   - [ ] Conversation context is created for new patient

3. **Check Odoo Integration (if connected):**
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'mcp_services/odoo_mcp')

   from healthcare_tools import get_patient_by_phone
   patient = get_patient_by_phone('+19998887777')
   print(f'Patient found: {patient is not None}')
   "
   ```

4. **Expected Workflow:**
   - AI detects new patient intent
   - Creates task in Needs_Action or Inbox
   - Draft includes warm welcome + registration steps
   - Phone number saved for follow-up

#### Success Criteria:
- New patient intent correctly identified
- Appropriate onboarding workflow triggered
- Patient data collected for registration

---

### Scenario 4: Approval Workflow End-to-End

**Objective**: Test the complete approval workflow from draft to execution.

#### Steps:

1. **Create Test Draft**
   ```bash
   # Simulate receiving a message (creates draft in Pending_Approval/)
   # See scenarios above for examples
   ```

2. **Review Draft**
   ```bash
   ls -la vault/Pending_Approval/
   cat vault/Pending_Approval/*.md
   ```

3. **Approve Draft**
   ```bash
   # Move draft to Approved/ folder
   mv vault/Pending_Approval/test-draft.md vault/Approved/
   ```

4. **Monitor Execution**
   ```bash
   # Check logs for execution
   tail -f vault/Logs/*.json

   # Check Done/ folder for completion
   ls -la vault/Done/
   ```

5. **Verify Results:**
   - [ ] Draft moved from Pending_Approval to Approved
   - [ ] Approval checker processed the draft
   - [ ] Message sent (or queued in DRY_RUN mode)
   - [ ] File moved to Done/ with status:sent

#### Success Criteria:
- Complete workflow executes without errors
- Messages sent only after approval
- Audit trail maintained in Done/ folder

---

### Scenario 5: Conversation Context Management

**Objective**: Verify conversation context is properly stored and retrieved.

#### Steps:

1. **Create Context**
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'backend')
   from backend.services.orchestrator import get_orchestrator

   orch = get_orchestrator()
   ctx = orch.create_conversation_context(
       conversation_id='test_ctx_001',
       patient_identifier='+1111111111',
       channel='whatsapp',
       language_detected='en',
       last_intent='appointment_booking',
       last_urgency='routine'
   )
   print(f'Context ID: {ctx[\"conversation_id\"]}')
   print(f'Language: {ctx[\"language_detected\"]}')
   "
   ```

2. **Add Messages**
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'backend')
   from backend.services.orchestrator import get_orchestrator

   orch = get_orchestrator()
   msg = orch.add_conversation_message(
       conversation_id='test_ctx_001',
       sender='patient',
       message_text='I need an appointment',
       urgency_classification='routine',
       intent_classification='appointment_booking',
       confidence_score=0.95
   )
   print(f'Message ID: {msg[\"id\"]}')
   "
   ```

3. **Retrieve History**
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'backend')
   from backend.services.orchestrator import get_orchestrator

   orch = get_orchestrator()
   history = orch.get_conversation_history('test_ctx_001')
   print(f'Messages: {len(history)}')
   for msg in history:
       print(f'  [{msg[\"sender\"]}]: {msg[\"message_text\"][:30]}...')
   "
   ```

#### Success Criteria:
- Context created and retrieved correctly
- Messages stored with classifications
- History retrieval works

---

### Scenario 6: Multi-Language Support (Optional)

**Objective**: Verify language detection and response generation.

#### Steps:

1. **Test Spanish Message**
   ```bash
   python -c "
   import asyncio
   import sys
   sys.path.insert(0, '..')

   from watchers.ai_integration import get_ai_integration

   async def test():
       ai = get_ai_integration()
       draft = await ai.triage_and_draft(
           message='Hola, necesito una cita para la próxima semana',
           channel='whatsapp',
           recipient='+521234567890'
       )
       print(f'Detected Language: {draft.language}')
       print(f'Response Language: {draft.draft_reply[:50]}...')

   asyncio.run(test())
   "
   ```

2. **Verify Results:**
   - [ ] Language correctly detected (Spanish)
   - [ ] Response in matching language
   - [ ] Confidence score reasonable

---

## Quick Test Script

Run the automated test script:

```bash
./scripts/test_healthcare_scenarios.sh
```

This will:
- Check prerequisites
- Test emergency detection
- Test routine classification
- Test new patient workflow
- Test conversation storage
- Test approval workflow

---

## Troubleshooting

### Issue: "ImportError: No module named 'watchers'"
**Solution**: Make sure you're running from the project root directory.

### Issue: "Database file not found"
**Solution**: Create the data directory:
```bash
mkdir -p backend/data/conversations
```

### Issue: "Odoo connection failed"
**Solution**: Check ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY in `.env`

### Issue: "Conversation context not retrieved"
**Solution**: Verify database path and permissions:
```bash
ls -la backend/data/conversations/
```

---

## Test Checklist Summary

Use this checklist to track your testing progress:

- [ ] Emergency detection (Scenario 1)
- [ ] Routine appointment (Scenario 2)
- [ ] New patient onboarding (Scenario 3)
- [ ] Approval workflow (Scenario 4)
- [ ] Conversation context (Scenario 5)
- [ ] Multi-language support (Scenario 6, optional)
- [ ] Automated test script execution

---

## Next Steps After Testing

1. **Review Logs**: Check `vault/Logs/` for any errors
2. **Clean Up Test Data**: Remove test conversations from database
3. **Document Findings**: Note any issues or improvements needed
4. **Prepare for Production**: Set `DRY_RUN=false` when ready for live testing

---

## Notes

- Always use `DRY_RUN=true` for testing unless specifically testing live execution
- Monitor log files in real-time: `tail -f vault/Logs/$(date +%Y-%m-%d).json`
- Test with both WhatsApp and email channels if configured
- Verify Odoo EHR records are created when connected
