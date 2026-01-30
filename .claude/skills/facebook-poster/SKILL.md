---
name: facebook-poster
description: Post content to Facebook Page via MCP server with approval workflow. Use when Claude needs to (1) create Facebook Page posts on behalf of the user, (2) draft social media content for approval, (3) share business updates, or (4) publish promotional content. ALWAYS requires human approval before posting.
---

# Facebook Page Poster

Post to Facebook Page via MCP with mandatory approval workflow.

## MCP Tool

```
Tool: facebook_post_to_page
Parameters:
  - content: string (post text)
  - link: string (optional, URL to share)
```

## Approval Workflow

**All Facebook posts require human approval before publishing.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't post
4. **Execute via MCP**: Call `facebook_post_to_page` tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

```markdown
---
type: facebook_post
status: pending_approval
created: {{ISO_DATE}}
---

# Facebook Post Approval Request

**Link:** {{URL if any, or "None"}}

## Post Content
{{The full post content}}

## Target Audience
{{Who this post is for}}

## Context
{{Why this post is being made, campaign/goal}}

## Approval
- [ ] Approved by CEO
```

## Best Practices

- Keep posts engaging and conversational
- Use emojis sparingly but appropriately
- Best posting times: 9 AM - 3 PM weekdays
- Include images when possible (via link)
- Include call-to-action when appropriate
- Consider Facebook's algorithm preferences

## Additional Read-Only Tools

These tools don't require approval:

- `facebook_get_page_insights` - Get page analytics
- `facebook_get_page_notifications` - Get recent activity
- `facebook_get_page_info` - Get page information
- `facebook_check_connection` - Verify API connection

## Rules

- NEVER post without approval file in Approved folder
- Check DRY_RUN environment variable before actual post
- Log all post attempts in vault/Logs/
- Monitor engagement after posting
- Respect Facebook's content policies
- Do not post copyrighted content without permission
