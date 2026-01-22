---
skill_name: Post LinkedIn
version: 1.0
requires_approval: true
mcp_tool: linkedin_post
---

# SKILL: Post to LinkedIn

## Purpose
Create LinkedIn posts using the MCP LinkedIn server.

## Inputs
- `content`: Post content (text)
- `visibility`: "PUBLIC" | "CONNECTIONS" (default: PUBLIC)
- `media_url`: (optional) URL to image or video

## Approval Requirement
**This skill ALWAYS requires human approval before execution.**

Before posting:
1. Create draft in vault/Pending_Approval/
2. Wait for file to be moved to vault/Approved/
3. Only then execute via MCP tool

## MCP Tool
```
Tool: linkedin_post
Parameters:
  - content: string
  - visibility: string
  - media_url: string (optional)
```

## Approval File Format
```markdown
---
type: linkedin_post
status: pending_approval
created: {{ISO_DATE}}
---

# LinkedIn Post Approval Request

**Visibility:** PUBLIC

## Post Content
{{The full post content}}

## Hashtags
{{Suggested hashtags}}

## Context
{{Why this post is being made, what campaign/goal}}

## Approval
- [ ] Approved by CEO
```

## Best Practices
- Keep posts under 3000 characters
- Use 3-5 relevant hashtags
- Best posting times: Tue-Thu, 8-10 AM
- Include call-to-action when appropriate

## Rules
- NEVER post without approval
- Check DRY_RUN flag before actual post
- Log all posts in vault/Logs/
- Track engagement metrics if available
