---
name: weekly-briefing
description: Generate executive weekly briefing reports for the CEO. Use when Claude needs to (1) summarize the week's completed tasks, (2) report on pending and in-progress work, (3) identify bottlenecks or delays, or (4) provide actionable recommendations.
---

# Weekly Briefing

Generate executive summaries of weekly activity using the Gold Tier CEO Briefing system.

## Data Sources

- `$VAULT_PATH/Dashboard.md` - Current status
- `$VAULT_PATH/Done/` - Completed tasks (filter by date)
- `$VAULT_PATH/Needs_Action/` - In-progress tasks
- `$VAULT_PATH/Pending_Approval/` - Awaiting approval
- `$VAULT_PATH/Logs/` - Activity history
- `$VAULT_PATH/Audit/` - Comprehensive audit trail
- API endpoints: `/api/audit/analytics`, `/api/ralph/status`

## Output Format

Uses the comprehensive CEO Briefing format with advanced analytics and insights.

## Workflow

1. **Call CEO Briefing API**: Use `/api/ceo-briefing/generate` endpoint
2. **Retrieve generated report**: Get from `/api/ceo-briefing/latest`
3. **Save report**: Write to `$VAULT_PATH/Reports/CEO_Briefing_{{DATE}}.md`

## Rules

- Use the enhanced CEO Briefing system for comprehensive reporting
- Include communication metrics from all platforms (Gmail, WhatsApp, LinkedIn)
- Include Ralph Wiggum performance metrics
- Include audit summary and system health status
- Include cross-domain insights and trend analysis
- Highlight actionable items requiring CEO attention
- Provide forward-looking recommendations
