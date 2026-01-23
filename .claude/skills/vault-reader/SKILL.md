---
name: vault-reader
description: Read and summarize Markdown files from the Obsidian vault. Use when Claude needs to (1) read task files from vault folders (Inbox, Needs_Action, Pending_Approval, Done), (2) get summaries of vault contents, (3) extract action items from tasks, (4) read the Dashboard or Company Handbook, or (5) list files in vault directories.
---

# Vault Reader

Read-only skill for accessing Obsidian vault contents.

## Vault Structure

```
$VAULT_PATH/
├── Inbox/           # New incoming tasks
├── Needs_Action/    # Tasks being processed
├── Pending_Approval/ # Actions awaiting human approval
├── Approved/        # Approved actions ready to execute
├── Done/            # Completed tasks
├── Logs/            # Activity logs
├── Plans/           # Generated plans and briefings
├── Dashboard.md     # Current status overview
└── Company_Handbook.md # Rules and guidelines
```

## Workflow

1. **Identify target**: Determine file path or folder name
2. **Read content**: Use file read tools to access .md files
3. **Parse frontmatter**: Extract YAML metadata between `---` markers
4. **Extract action items**: Find lines starting with `- [ ]` or `- [x]`
5. **Return structured summary**: Include metadata, content summary, and action items

## Frontmatter Format

Task files use this frontmatter structure:
```yaml
---
created: 2026-01-22T10:00:00Z
priority: high | medium | low
status: new | processing | awaiting_approval | approved | completed
tags: [tag1, tag2]
---
```

## Summary Types

- **full**: Complete file content with all details
- **brief**: 2-3 sentence summary with key points
- **actionable**: Only pending action items (`- [ ]`)

## Rules

- READ-ONLY: Never modify files during read operations
- Report missing files honestly, never assume content
- Always check `$VAULT_PATH` environment variable for vault location
- Parse and return frontmatter metadata when present
