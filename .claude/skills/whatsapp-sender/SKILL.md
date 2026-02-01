---
name: whatsapp-sender
description: Send WhatsApp messages via MCP server with approval workflow. Use when Claude needs to (1) send WhatsApp messages on behalf of the user, (2) create message drafts for approval, (3) respond to WhatsApp contacts, or (4) send notifications via WhatsApp. ALWAYS requires human approval before sending.
---

# WhatsApp Sender

Send WhatsApp messages via MCP with mandatory approval workflow.

## MCP Tools

```
Tool: mcp__whatsapp__send_message
Parameters:
  - phone: string (with country code, e.g., +1234567890)
  - message: string (the message content)

Tool: mcp__whatsapp__check_session
Parameters: none
Returns: Session status (active or needs QR scan)

Tool: mcp__whatsapp__get_unread_count
Parameters: none
Returns: Number of unread chat conversations
```

## Quick Commands

- **Send message**: `mcp__whatsapp__send_message(phone="+923001234567", message="Hello!")`
- **Check session**: `mcp__whatsapp__check_session()`
- **Get unreads**: `mcp__whatsapp__get_unread_count()`

## Approval Workflow

**All WhatsApp messages require human approval before sending.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't send
4. **Execute via MCP**: Call `whatsapp_send_message` tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

```markdown
---
type: whatsapp_send
status: pending_approval
created: {{ISO_DATE}}
---

# WhatsApp Message Approval Request

**To:** +1234567890
**Contact Name:** {{if known}}

## Message
{{The full message content}}

## Context
{{Why this message is being sent, what task it relates to}}

## Approval
- [ ] Approved by CEO
```

## Phone Number Format

- Must include country code
- Format: `+[country_code][number]`
- Examples: `+14155551234`, `+923001234567`

## Session Requirements

- WhatsApp Web session must be active
- First run requires QR code scan
- Session stored in `$WHATSAPP_SESSION_PATH`
- Session may expire and need re-authentication

## Troubleshooting

**Session not detected even after QR scan:**
1. Kill existing browser: `pkill -f "chrome.*whatsapp_session"`
2. Call `mcp__whatsapp__check_session()` to open fresh browser
3. Scan QR code in the new window
4. Wait for chats to load before sending

**Browser window not visible:**
- Check `WHATSAPP_HEADLESS` env var is set to `"false"`
- Look for Chromium window in taskbar

**Message send fails:**
- Verify phone number includes country code (+XX format)
- Ensure WhatsApp Web shows your chats (logged in state)
- Check if the contact exists on WhatsApp

## Rules

- NEVER send without approval file in Approved folder
- Verify phone number format before creating approval request
- Check DRY_RUN environment variable before actual send
- Log all send attempts in vault/Logs/
- Report session errors clearly to user
