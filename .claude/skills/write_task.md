---
skill_name: Write Task
version: 1.0
---

# SKILL: Write Task

## Purpose
Create or update task files in the vault.

## Inputs
- `title`: Task title (becomes filename slug)
- `description`: Task details
- `priority`: "high" | "medium" | "low"
- `target_folder`: "Inbox" | "Needs_Action" | "Done"
- `tags`: List of tags (optional)

## Outputs
- New/updated .md file in target folder
- Confirmation message with file path

## File Format
```markdown
---
created: {{ISO_DATE}}
priority: {{PRIORITY}}
status: pending
tags: [{{TAGS}}]
---

# {{TITLE}}

## Description
{{DESCRIPTION}}

## Action Items
- [ ] Item 1

## Notes
<!-- AI processing notes go here -->
```

## Rules
- One task per file
- Timestamp every entry
- Use slug format for filenames (lowercase, hyphens)
- Never overwrite without explicit instruction
- Log creation in vault/Logs/

## Example Usage
```
Create a new task:
- Title: "Follow up with client"
- Description: "Send project update email to client@example.com"
- Priority: high
- Tags: [email, client, urgent]
```
