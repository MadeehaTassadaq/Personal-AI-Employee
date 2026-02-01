---
name: linkedin-poster
description: Post content to LinkedIn via MCP server with approval workflow. Use when Claude needs to (1) create LinkedIn posts on behalf of the user, (2) draft social media content for approval, (3) share professional updates, or (4) publish thought leadership content. ALWAYS requires human approval before posting.
---

# LinkedIn Poster

Post to LinkedIn via MCP with mandatory approval workflow.

## MCP Tool

```
Tool: mcp__linkedin__create_post
Parameters:
  - content: string (required, post text)
  - visibility: string ("PUBLIC" | "CONNECTIONS", default: "PUBLIC")
  - image_url: string (optional, URL to an image to include)
  - link_url: string (optional, URL to a link/article to share)
```

## Image Posting

To post with an image:
1. Ensure the image URL is publicly accessible
2. Pass the URL via `image_url` parameter
3. LinkedIn will fetch and display the image as a preview

Example with image:
```
mcp__linkedin__create_post(
  content="Check out our new AI workspace!",
  image_url="https://example.com/image.jpg",
  visibility="PUBLIC"
)
```

## Approval Workflow

**All LinkedIn posts require human approval before publishing.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't post
4. **Execute via MCP**: Call `linkedin_post` tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

```markdown
---
type: linkedin_post
status: pending_approval
created: {{ISO_DATE}}
---

# LinkedIn Post Approval Request

**Visibility:** PUBLIC | CONNECTIONS
**Media:** {{URL if any, or "None"}}

## Post Content
{{The full post content}}

## Hashtags
{{Suggested hashtags}}

## Context
{{Why this post is being made, campaign/goal}}

## Approval
- [ ] Approved by CEO
```

## Best Practices

- Keep posts under 3000 characters
- Use 3-5 relevant hashtags
- Best posting times: Tuesday-Thursday, 8-10 AM
- Include call-to-action when appropriate
- Professional tone aligned with user's brand

## Rules

- NEVER post without approval file in Approved folder
- Check DRY_RUN environment variable before actual post
- Log all post attempts in vault/Logs/
- Track engagement metrics if available from MCP
- Respect LinkedIn's content policies
