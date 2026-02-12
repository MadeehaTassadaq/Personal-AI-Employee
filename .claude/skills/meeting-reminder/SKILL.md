---
name: meeting-reminder
description: Send meeting reminders to attendees via WhatsApp/Email with approval workflow. Use when Claude needs to (1) send reminders for upcoming meetings, (2) notify attendees of schedule changes, or (3) follow up on meeting actions. ALWAYS requires human approval before sending.
---

# Meeting Reminder

Send meeting reminders to attendees via WhatsApp or Email with mandatory approval workflow.

## MCP Tools

### Calendar Tools
```
Tool: mcp__calendar__list_events
Parameters:
  - days: integer (number of days to look ahead, default: 1)
  - max_results: integer (max events to return, default: 20)

Tool: mcp__calendar__get_today_events
Parameters: none
```

### WhatsApp Tools
```
Tool: mcp__whatsapp__send_message
Parameters:
  - phone: string (with country code, e.g., +1234567890)
  - message: string (the message content)
```

### Email Tools
```
Tool: mcp__gmail__send_email
Parameters:
  - to: string (recipient email address)
  - subject: string (email subject line)
  - body: string (email body text)
  - cc: string (optional CC recipients)
  - bcc: string (optional BCC recipients)
```

## Approval Workflow

**All meeting reminders require human approval before sending.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't send
4. **Execute via MCP**: Call appropriate messaging tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

### For Meeting Reminders

```markdown
---
type: meeting_reminder
status: pending_approval
created: {{ISO_DATE}}
platform: whatsapp
---

# Meeting Reminder: {{Event Title}}

**When:** {{YYYY-MM-DD HH:MM AM/PM}}
**Attendees:** {{List of attendees with phone/emails}}

## Meeting Details
- **Title:** {{Event title}}
- **Time:** {{Start time to End time}}
- **Location:** {{Location if any}}
- **Description:** {{Event description}}

## Reminder Message
{{Proposed reminder message to send}}

## Approval
- [ ] Approved by CEO
- [ ] Message reviewed
- [ ] Ready to send
```

### For Batch Reminders

```markdown
---
type: meeting_reminder_batch
status: pending_approval
created: {{ISO_DATE}}
platform: whatsapp
---

# Batch Meeting Reminders - {{Date}}

**Total Reminders:** {{Count}}
**Scheduled Time:** {{Time when reminders should be sent}}

## Reminders to Send

### Reminder 1: {{Meeting Title}}
- **To:** {{Attendee 1}} ({{Phone/Email}})
- **Meeting:** {{Meeting details}}
- **Message:** {{Reminder message}}

### Reminder 2: {{Meeting Title}}
- **To:** {{Attendee 2}} ({{Phone/Email}})
- **Meeting:** {{Meeting details}}
- **Message:** {{Reminder message}}

{{Add more reminders as needed...}}

## Approval
- [ ] Approved by CEO
- [ ] All messages reviewed
- [ ] Ready to send batch
```

## Reminder Message Templates

### Standard Reminder (24 Hours Before)
```
Hi! Reminder about our meeting "{{Meeting Title}}" tomorrow at {{Time}}.

Looking forward to it! Let me know if you need to reschedule.
```

### Same-Day Reminder
```
Hi! Just a reminder about our meeting "{{Meeting Title}}" today at {{Time}}.

See you then!
```

### Follow-Up Reminder (After Meeting)
```
Hi! Great meeting earlier today. Here's a quick recap:

{{Key discussion points}}
{{Action items}}
{{Next steps}}

Thanks!
```

## Daily Scheduler Integration

The meeting reminder system integrates with the daily scheduler:

- **8:00 AM Daily**: Checks calendar for meetings in next 24 hours
- **Creates approval tasks** in `Pending_Approval/`
- **User approves** to send reminders
- **Reminders sent** via WhatsApp or Email

## Filename Convention

`meeting_reminder-{{slug}}-{{DATE}}.md`

Examples:
- `meeting_reminder-team-standup-2026-02-12.md`
- `meeting_reminder_client-review-2026-02-12.md`
- `meeting_reminder_batch-2026-02-12.md`

## Usage Examples

### Check Today's Meetings
```
1. Use mcp__calendar__get_today_events tool
2. Parse returned events
3. Identify which events need reminders
4. Create reminder tasks in Pending_Approval/
```

### Check Tomorrow's Meetings
```
1. Use mcp__calendar__list_events with days=2
2. Filter events for tomorrow
3. Create reminder tasks for each
```

### Send WhatsApp Reminder
```
1. Create approval file with attendee phone numbers
2. Wait for approval
3. Call mcp__whatsapp__send_message for each attendee
4. Log results
```

### Send Email Reminder
```
1. Create approval file with attendee emails
2. Wait for approval
3. Call mcp__gmail__send_email with recipients
4. Use BCC for multiple recipients
5. Log results
```

## Contact Information Handling

### WhatsApp
- Get phone numbers from event attendees
- Must include country code format: +XX
- Send individual messages to each attendee
- Consider group chat for team meetings

### Email
- Get email addresses from event attendees
- Use CC for relevant team members
- Use BCC for larger groups to protect privacy
- Include event details in body

## Rules

- NEVER send reminders without approval file in Approved folder
- Verify phone/email format before creating approval request
- Check DRY_RUN environment variable before actual send
- Log all send attempts in vault/Logs/
- Include meeting time zone in reminders
- Consider attendee preferences (WhatsApp vs Email)
- Don't send reminders for past meetings
- Handle MCP errors gracefully and report to user
- For recurring meetings, note recurrence in reminder

## Automation Schedule

The daily scheduler automatically:
1. Runs at 8:00 AM every day
2. Scans calendar for next 24 hours of meetings
3. Creates reminder tasks for each meeting
4. Places tasks in Pending_Approval folder
5. Awaits human approval before sending

Manual triggers can be done via:
- Dashboard compose panel
- Direct task file creation
- API endpoint trigger
