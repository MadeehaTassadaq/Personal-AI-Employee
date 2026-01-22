---
skill_name: Send WhatsApp
version: 1.0
requires_approval: true
mcp_tool: whatsapp_send_message
---

# SKILL: Send WhatsApp Message

## Purpose
Send WhatsApp messages using the MCP WhatsApp server (Playwright-based).

## Inputs
- `phone`: Phone number (with country code, e.g., +1234567890)
- `message`: Message content

## Approval Requirement
**This skill ALWAYS requires human approval before execution.**

Before sending:
1. Create draft in vault/Pending_Approval/
2. Wait for file to be moved to vault/Approved/
3. Only then execute via MCP tool

## MCP Tool
```
Tool: whatsapp_send_message
Parameters:
  - phone: string (with country code)
  - message: string
```

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
{{Why this message is being sent}}

## Approval
- [ ] Approved by CEO
```

## Rules
- NEVER send without approval
- Verify phone number format
- Check DRY_RUN flag before actual send
- Log all sends in vault/Logs/
- Note: WhatsApp Web session must be active

## Session Requirements
- First run requires QR code scan
- Session stored in WHATSAPP_SESSION_PATH
- Session may expire and need re-authentication
