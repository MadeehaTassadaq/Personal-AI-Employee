---
name: social-content-creator
description: Generate platform-specific social media content for LinkedIn, Facebook, Instagram, and Twitter. Use when Claude needs to (1) create social media posts, (2) generate platform-appropriate content with hashtags, (3) create content calendars, or (4) draft engaging posts for approval.
---

# Social Content Creator

Generate platform-optimized social media content with appropriate tone, formatting, and hashtags.

## Supported Platforms

### LinkedIn
- **Tone**: Professional, thought leadership, industry insights
- **Length**: 150-300 words optimal, up to 3000 characters
- **Format**: Hook → Value → CTA, space-separated paragraphs
- **Hashtags**: 3-5 relevant hashtags
- **Best posting times**: Tuesday-Thursday, 8-10 AM or 5-6 PM

### Facebook
- **Tone**: Conversational, community-focused, engaging
- **Length**: 40-80 characters for best engagement
- **Format**: Question or statement inviting engagement
- **Hashtags**: 1-2 hashtags optional
- **Best posting times**: Wednesday, 1-4 PM

### Instagram
- **Tone**: Engaging, visual-focused, storytelling
- **Length**: Under 2200 characters
- **Format**: Attention-grabbing first line → Story → CTA
- **Hashtags**: Up to 30 hashtags (mix of popular and niche)
- **Best posting times**: Monday-Friday, 11 AM-1 PM

### Twitter/X
- **Tone**: Concise, timely, conversational
- **Length**: Under 280 characters (or thread for longer)
- **Format**: Hook → Value → CTA in single tweet
- **Hashtags**: 1-2 hashtags
- **Best posting times**: Wednesday-Friday, 9 AM-12 PM

## Content Types

### Educational
- Industry tips and tricks
- How-to guides
- Best practices
- Myth-busting

### Behind-the-Scenes
- Company culture
- Team highlights
- Work process
- Day in the life

### Industry News
- Trend commentary
- News analysis
- Market updates
- Technology advances

### Product/Service Highlights
- Feature announcements
- Case studies
- Testimonials
- Success stories

### Engagement Posts
- Questions
- Polls
- This or That
- Fill in the blank

## Content Templates

### Monday Motivation
```
{{Motivational quote or insight}}

{{Brief elaboration}}

{{Question to engage audience}}

{{Hashtags}}
```

### Wednesday Tips
```
{{Topic}} Tip #{{Number}}:

{{The tip}}

{{Why it matters}}

{{CTA: Save this for later or share with someone who needs it}}

{{Hashtags}}
```

### Friday Fun
```
{{Lighthearted industry joke or relatable moment}}

{{Engagement question}}

{{Hashtags}}
```

### Product Launch
```
{{Exciting announcement}}

{{Problem it solves}}

{{Key benefit}}

{{CTA: Link in bio or Learn more}}

{{Hashtags}}
```

### Thought Leadership
```
{{Provocative statement or question}}

{{Your unique perspective}}

{{Supporting evidence or story}}

{{CTA: Thoughts?}}

{{Hashtags}}
```

## Approval File Format

```markdown
---
type: social_post
platform: {{PLATFORM}}
status: pending_approval
created: {{ISO_DATE}}
content_type: {{TYPE}}
scheduled_for: {{OPTIONAL_DATE}}
---

# {{Platform}} Post Request

## Content Type
{{Educational, Behind-the-Scenes, Industry News, etc.}}

## AI-Generated Content

### Post
{{Generated post content}}

### Hashtags
{{Generated hashtags}}

### Image Suggestions
{{Optional: Suggest image type or description}}

### Link URL (optional)
{{URL to share if applicable}}

## Scheduling
- **Best time to post**: {{Optimal posting time}}
- **Frequency**: {{How often to post similar content}}

## Review Required
- Edit content as needed before approving
- Move to Approved/ to schedule/publish
- Move to Done/ to reject
```

## MCP Tools

```
LinkedIn: linkedin_create_post
Parameters:
  - content: string
  - visibility: "PUBLIC" | "CONNECTIONS"
  - link_url: string (optional)

Facebook: facebook_post_to_page
Parameters:
  - content: string
  - link: string (optional)

Instagram: instagram_post_image
Parameters:
  - image_url: string (public URL required)
  - caption: string

Twitter: twitter_create_tweet
Parameters:
  - content: string
```

## Ralph Integration

1. **User creates task** → "Create LinkedIn post about AI trends"
2. **Ralph picks up task** → calls social-content-creator
3. **Skill generates content** → platform-specific post with hashtags
4. **Creates approval file** → Pending_Approval/social-post-*.md
5. **User reviews** → edits if needed
6. **User approves** → moves to Approved/
7. **Publisher executes** → posts via MCP
8. **File moved to Done** → with post ID for tracking

## Hashtag Strategy

### LinkedIn Hashtags (Professional)
```
#{{Industry}} #{{Niche}} #{{Topic}} #{{Benefit}}
Examples: #AI #MachineLearning #DigitalTransformation #TechTrends
```

### Instagram Hashtags (Mixed Reach)
```
#{{Popular}} (1-3M+ posts)
#{{Niche}} (100K-1M posts)
#{{Specific}} (10K-100K posts)
#{{Branded}} (custom)

Examples: #Entrepreneur #BusinessTips #AI #Automation #YourBrandName
```

### Twitter Hashtags (Trending)
```
#{{TrendingTopic}} OR #{{IndustryNiche}}

Examples: #AI #TechNews #StartupLife
```

## Content Calendar Integration

Generate weekly content calendar:

```markdown
# Weekly Social Media Content Calendar
Week of {{DATE}}

## Monday
- LinkedIn: {{Topic}}
- Instagram: {{Topic}}
- Facebook: {{Topic}}

## Tuesday
- LinkedIn: {{Topic}}
- Twitter: {{Topic}}

## Wednesday
- LinkedIn: {{Topic}}
- Instagram: {{Topic}}

## Thursday
- LinkedIn: {{Topic}}
- Facebook: {{Topic}}

## Friday
- LinkedIn: {{Topic}}
- Twitter: {{Topic}}
```

## Filename Convention

`social-{{platform}}-{{timestamp}}.md`

Examples:
- `social-linkedin-20260211.md`
- `social-instagram-20260211.md`
- `social-facebook-20260211.md`

## Rules

- Always adapt tone to platform (LinkedIn = professional, Instagram = casual)
- Include relevant hashtags for each platform
- Respect character limits (Twitter: 280, Instagram: 2200, LinkedIn: 3000)
- Create engaging hooks (first line is critical for engagement)
- Include clear CTA when appropriate
- Suggest image types for Instagram posts
- Schedule optimal posting times when possible
- All posts require approval before publishing
