---
skill_name: Move Task
version: 1.0
---

# SKILL: Move Task

## Purpose
Move task files between lifecycle folders.

## Inputs
- `file_path`: Current file location
- `destination`: "Inbox" | "Needs_Action" | "Pending_Approval" | "Approved" | "Done"
- `completion_notes`: Notes to add (required for Done)

## Outputs
- File moved to destination folder
- Status field updated in frontmatter
- Timestamp added for the move

## Rules
- Add processing notes when moving to Needs_Action
- Add completion summary when moving to Done
- Update Dashboard.md after each move
- Log the move in vault/Logs/
- Never skip lifecycle stages without reason

## Lifecycle Flow
```
Inbox → Needs_Action → Done (for auto-approved tasks)
                     ↓
            Pending_Approval → Approved → Done (for sensitive tasks)
```

## Status Updates
- To Inbox: status = "new"
- To Needs_Action: status = "processing"
- To Pending_Approval: status = "awaiting_approval"
- To Approved: status = "approved"
- To Done: status = "completed"

## Example Usage
```
Move vault/Inbox/client-followup.md to Needs_Action
Add note: "Analyzing email content and preparing response draft"
```
