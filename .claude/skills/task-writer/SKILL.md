---
name: task-writer
description: Create or update task files in the Obsidian vault. Use when Claude needs to (1) create new task files in Inbox or other folders, (2) update existing task content, (3) add notes or action items to tasks, or (4) generate task files from external inputs like emails or messages.
---

# Task Writer

Create and update task files in the Obsidian vault.

## Task File Format

```markdown
---
created: {{ISO_DATE}}
priority: high | medium | low
status: pending
tags: [tag1, tag2]
source: manual | email | whatsapp | linkedin
---

# {{TITLE}}

## Description
{{DESCRIPTION}}

## Action Items
- [ ] Item 1
- [ ] Item 2

## Notes
<!-- Processing notes added here -->

## History
- {{ISO_DATE}}: Created
```

## Workflow

1. **Generate filename**: Convert title to slug format (lowercase, hyphens)
2. **Set frontmatter**: Include created date, priority, status, tags, source
3. **Write content**: Add title, description, action items
4. **Save to target folder**: Default is `$VAULT_PATH/Inbox/`
5. **Log creation**: Add entry to `$VAULT_PATH/Logs/`

## Filename Convention

- Use slug format: `client-followup.md`, `quarterly-report.md`
- Lowercase letters, numbers, and hyphens only
- Max 50 characters
- Must be unique within the target folder

## Rules

- One task per file
- Always timestamp entries with ISO format
- Never overwrite existing files without explicit instruction
- Log all creations in vault/Logs/
- Default priority is "medium" if not specified
- Default status is "pending" for new tasks
