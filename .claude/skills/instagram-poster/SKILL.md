---
name: instagram-poster
description: Post images and carousels to Instagram Business account via MCP server with approval workflow. Use when Claude needs to (1) create Instagram posts on behalf of the user, (2) draft visual content for approval, (3) share brand imagery, or (4) publish promotional content. ALWAYS requires human approval before posting. NOTE - Images must be at publicly accessible URLs.
---

# Instagram Poster

Post to Instagram Business account via MCP with mandatory approval workflow.

## MCP Tools

```
Tool: instagram_post_image
Parameters:
  - image_url: string (PUBLIC URL of image - must be accessible by Instagram)
  - caption: string (post caption, max 2200 chars, max 30 hashtags)

Tool: instagram_post_carousel
Parameters:
  - image_urls: string (comma-separated PUBLIC URLs, 2-10 images)
  - caption: string (post caption)
```

## Image Requirements

**IMPORTANT**: Instagram fetches images from the provided URL. The URL must be:
- Publicly accessible (no authentication required)
- Direct link to an image file (JPEG recommended)
- Minimum 320x320 pixels, recommended 1080x1080
- Maximum file size: 8MB

## Approval Workflow

**All Instagram posts require human approval before publishing.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't post
4. **Execute via MCP**: Call `instagram_post_image` or `instagram_post_carousel`
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

```markdown
---
type: instagram_post
status: pending_approval
created: {{ISO_DATE}}
post_type: single | carousel
---

# Instagram Post Approval Request

**Post Type:** Single Image | Carousel
**Image URL(s):** {{comma-separated URLs}}

## Caption
{{The full caption including hashtags}}

## Hashtags (separate list)
{{Recommended hashtags}}

## Target Audience
{{Who this post is for}}

## Context
{{Why this post is being made, campaign/goal}}

## Approval
- [ ] Approved by CEO
- [ ] Image reviewed for brand guidelines
```

## Best Practices

- Use high-quality, visually appealing images
- Write engaging captions that tell a story
- Use 5-15 relevant hashtags (mix of popular and niche)
- Best posting times: 11 AM - 1 PM and 7 PM - 9 PM
- Include call-to-action in caption
- Use carousel for multi-image stories

## Caption Guidelines

- First line should hook the viewer
- Break up text with emojis or line breaks
- End with a question or CTA
- Put hashtags at the end or in first comment

## Additional Read-Only Tools

These tools don't require approval:

- `instagram_get_insights` - Get account analytics
- `instagram_get_media` - Get recent posts
- `instagram_get_account_info` - Get account information
- `instagram_check_connection` - Verify API connection

## Rules

- NEVER post without approval file in Approved folder
- Check DRY_RUN environment variable before actual post
- Verify image URLs are accessible before posting
- Log all post attempts in vault/Logs/
- Respect Instagram's content policies
- Only use images you have rights to
