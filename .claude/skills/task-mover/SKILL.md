---
name: task-mover
description: Move task files between lifecycle folders in the Obsidian vault. Use when Claude needs to (1) transition tasks through the workflow (Inbox to Needs_Action to Done), (2) send tasks for approval, (3) mark tasks as completed, or (4) update task status in frontmatter.
---

# Task Mover

Move task files through the lifecycle workflow.

## Lifecycle Folders

```
Inbox → Needs_Action → Done                    (auto-approved tasks)
                     ↓
              Pending_Approval → Approved → Done  (sensitive tasks)
```

## Status Mapping

| Folder            | Status            |
|-------------------|-------------------|
| Inbox             | new               |
| Needs_Action      | processing        |
| Pending_Approval  | awaiting_approval |
| Approved          | approved          |
| Done              | completed         |

## Workflow

1. **Read source file**: Get current content and frontmatter
2. **Update frontmatter**: Change status field to match destination
3. **Add timestamp**: Record move time in History section
4. **Add notes**: Include processing or completion notes
5. **Move file**: Transfer to destination folder
6. **Update Dashboard**: Refresh `$VAULT_PATH/Dashboard.md`
7. **Log move**: Add entry to `$VAULT_PATH/Logs/`

## Required Notes

- **To Needs_Action**: Add processing notes (what will be done)
- **To Pending_Approval**: Add context for approver
- **To Done**: Add completion summary (required)

## Move Examples

```bash
# Auto-approved task flow
Inbox/task.md → Needs_Action/task.md → Done/task.md

# Approval-required task flow
Inbox/task.md → Needs_Action/task.md → Pending_Approval/task.md
Pending_Approval/task.md → Approved/task.md → Done/task.md
```

## Rules

- Always add timestamp when moving
- Completion notes required when moving to Done
- Update Dashboard.md after every move
- Log all moves in vault/Logs/
- Never skip lifecycle stages without documented reason
