---
name: email-analyzer
description: Analyze incoming emails from Gmail to categorize, extract action items, and prioritize. Use when Claude needs to (1) process new emails, (2) categorize emails by type (urgent, inquiry, newsletter, etc.), (3) extract action items and deadlines from emails, or (4) determine if an email requires a response.
---

# Email Analyzer

Intelligent email analysis skill for automated email processing and categorization.

## Capabilities

### Email Categorization
- **Urgent**: Time-sensitive requests, deadline-driven, keywords (urgent, asap, emergency)
- **Client Inquiry**: Business questions, service requests, potential leads
- **Newsletter**: Marketing content, newsletters, notifications (auto-archive)
- **Internal**: Team communications, internal updates
- **Complaint**: Customer complaints, negative feedback (high priority)
- **Follow-up Required**: Emails needing future action or response

### Action Item Extraction
- Identify tasks from email content
- Extract deadlines and due dates
- Detect meeting requests and appointments
- Find calls to action (CTAs)

### Priority Assessment
- **High**: Urgent, complaints, client inquiries, deadline-driven
- **Medium**: Follow-ups, internal communications
- **Low**: Newsletters, general updates, FYI items

## MCP Tool

```
Tool: gmail_search_emails
Parameters:
  - query: string (Gmail search query)
  - max_results: integer (default: 10)

Tool: gmail_mcp__send_email (for responses)
Parameters:
  - to: string
  - subject: string
  - body: string
```

## Analysis Workflow

1. **Connect to Gmail API**: Use MCP to fetch new emails
2. **Parse Email Content**:
   - Sender (from address)
   - Subject line
   - Body content
   - Attachments
   - Timestamp
3. **Categorize Email**: Apply categorization rules
4. **Extract Action Items**: Parse for tasks and deadlines
5. **Determine Response Needed**: Boolean decision
6. **Create Vault Task**: Generate task file in appropriate folder

## Task File Format

```markdown
---
type: email_analysis
email_id: {{GMAIL_MESSAGE_ID}}
category: {{CATEGORY}}
priority: {{PRIORITY}}
status: inbox
response_needed: true/false
created: {{ISO_DATE}}
deadline: {{DEADLINE_IF_ANY}}
sender: {{SENDER_EMAIL}}
subject: {{EMAIL_SUBJECT}}
---

# Email Analysis: {{Subject}}

## Email Details
- **From:** {{Sender Name}} <{{email}}>
- **Date:** {{Received Date}}
- **Category:** {{Category}}
- **Priority:** {{Priority}}

## Summary
{{Brief 2-3 sentence summary of email content}}

## Action Items
{{Extracted action items as checkboxes}}
- [ ] {{Action 1}}
- [ ] {{Action 2}}

## Deadline
{{Extracted deadline or "None"}}

## Response Strategy
{{Suggested response approach if reply needed}}

## Original Email
{{Full email content or snippet}}
```

## Categorization Rules

### Urgent Keywords
```
urgent, asap, emergency, immediately, deadline, time-sensitive,
critical, important, priority, pressing
```

### Client Inquiry Patterns
```
question, inquiry, interested in, pricing, quote, proposal,
can you, would you, wondering about, help with
```

### Newsletter Patterns
```
unsubscribe, newsletter, digest, weekly, monthly, update,
notification, alert, blog post
```

### Complaint Patterns
```
issue, problem, not working, broken, error, complaint,
disappointed, unhappy, refund, dissatisfied
```

### Deadline Extraction
```
by {date}, before {date}, due {date}, need by {date},
deadline {date}, end of day, EOD, end of week, EOW
```

## Ralph Integration

The email analyzer is integrated with Ralph Wiggum's autonomous processing:

1. **Gmail Watcher** detects new emails → creates inbox task
2. **Ralph** picks up email task → calls email-analyzer
3. **Email Analyzer** → categorizes and creates structured task
4. **Ralph** → generates draft response if needed (via ai_reasoning)
5. **Approval** → user reviews and approves response
6. **Publisher** → sends approved response via Gmail MCP

## Filename Convention

`email-analysis-{{timestamp}}-{{category}}.md`

Examples:
- `email-analysis-20260211-client-inquiry.md`
- `email-analysis-20260211-urgent-deadline.md`

## Rules

- Always analyze full email content, not just subject
- Extract and preserve deadline information
- Flag emails from VIP senders (clients, management)
- Create checkbox action items for clarity
- Suggest response strategy when reply is needed
- Archive newsletters automatically to Done/ folder
- High priority for client-facing communications
