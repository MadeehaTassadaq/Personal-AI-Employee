---
name: twitter-poster
description: Post tweets to Twitter/X via MCP server with approval workflow. Use when Claude needs to (1) create tweets on behalf of the user, (2) draft social media content for approval, (3) share quick updates, or (4) engage with trending topics. ALWAYS requires human approval before posting. Max 280 characters per tweet.
---

# Twitter/X Poster

Post to Twitter/X via MCP with mandatory approval workflow.

## MCP Tool

```
Tool: twitter_post_tweet
Parameters:
  - content: string (tweet text, MAX 280 characters)
  - reply_to: string (optional, tweet ID to reply to)
```

## Character Limits

- **280 characters maximum** for tweet content
- URLs count as 23 characters regardless of length
- Media attachments use additional characters
- @ mentions count toward limit

## Approval Workflow

**All tweets require human approval before publishing.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't post
4. **Execute via MCP**: Call `twitter_post_tweet` tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Approval File Format

```markdown
---
type: twitter_post
status: pending_approval
created: {{ISO_DATE}}
character_count: {{number}}
---

# Twitter Post Approval Request

**Character Count:** {{X}}/280
**Reply To:** {{tweet ID if reply, or "Original tweet"}}

## Tweet Content
{{The exact tweet content}}

## Context
{{Why this tweet is being made, trending topic, campaign}}

## Hashtags (included in content)
{{List of hashtags used}}

## Approval
- [ ] Approved by CEO
```

## Best Practices

- Keep tweets concise and punchy
- Use 1-2 relevant hashtags max
- Best posting times: 9 AM, 12 PM, 5 PM weekdays
- Engage with trending topics when relevant
- Include a hook in the first few words
- Use threads for longer content

## Tweet Formatting Tips

- Start with the most important information
- Use line breaks for readability (counts as characters)
- Emojis add personality but use sparingly
- Tag relevant accounts when appropriate
- Include links at the end

## Thread Strategy

For content longer than 280 characters:
1. Create approval request for entire thread
2. Break content into multiple tweets
3. Each tweet should stand alone somewhat
4. Number tweets (1/5, 2/5, etc.) or use 🧵

## Additional Read-Only Tools

These tools don't require approval:

- `twitter_get_mentions` - Get mentions of account
- `twitter_get_timeline` - Get home timeline
- `twitter_get_analytics` - Get tweet performance
- `twitter_get_user_info` - Get account information
- `twitter_check_connection` - Verify API connection

## Rules

- NEVER post without approval file in Approved folder
- Check DRY_RUN environment variable before actual post
- Verify tweet is under 280 characters
- Log all post attempts in vault/Logs/
- Respect Twitter's content policies
- Do not engage in spam or harassment
- Be mindful of brand voice consistency
