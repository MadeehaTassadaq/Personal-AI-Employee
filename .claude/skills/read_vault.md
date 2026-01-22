---
skill_name: Read Vault
version: 1.0
---

# SKILL: Read Vault

## Purpose
Read Markdown files from the Obsidian vault and summarize relevant information.

## Inputs
- `path`: File path OR folder name (e.g., "Inbox", "vault/Dashboard.md")
- `summary_type`: "full" | "brief" | "actionable"

## Outputs
- Structured summary of file contents
- List of action items (if any)
- Metadata (dates, tags, status)

## Rules
- READ-ONLY operation
- Never modify files during read
- Report missing files, don't assume content
- Extract frontmatter metadata if present

## Example Usage
```
Read the file vault/Needs_Action/client_followup.md
Provide a brief summary with action items.
```

## Implementation
1. Check if path exists
2. If folder: list all .md files
3. If file: read content
4. Parse frontmatter (YAML between ---)
5. Extract action items (lines starting with - [ ])
6. Return structured response
