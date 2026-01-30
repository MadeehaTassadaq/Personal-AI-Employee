# CEO Briefing - Gold Tier

Generate a comprehensive CEO briefing report with enhanced insights.

## Trigger
- User asks for "CEO briefing" or "executive summary"
- Scheduled: Monday 9 AM (weekly briefing)

## Output
Generate report to: `AI_Employee_Vault/Reports/CEO_Briefing_YYYY-MM-DD.md`

## Report Sections

### 1. Executive Summary
- One paragraph overview of the week
- Key metrics at a glance
- Critical items requiring attention

### 2. Communication Metrics
**Email (Gmail)**
- Total emails received/sent
- Response rate
- Key threads to monitor
- Pending responses > 24h

**WhatsApp**
- Messages received/sent
- Active conversations
- Items requiring follow-up

**LinkedIn**
- Connection requests
- Message engagement
- Post performance (if applicable)

### 3. Task Pipeline
- Inbox count
- Tasks in progress
- Completed this week
- Blocked/stalled items
- Approval queue status

### 4. Ralph Wiggum Loop Performance
- Tasks auto-processed
- Success rate
- Average steps per task
- Errors/failures

### 5. Audit Summary
- Total audit events
- Errors/warnings count
- Platform health status
- Notable incidents

### 6. Cross-Domain Insights
Analyze patterns across platforms:
- Communication velocity trends
- Task completion trends
- Platform usage patterns
- Potential bottlenecks

### 7. Action Items
Prioritized list of recommended actions:
- [ ] Critical (immediate attention)
- [ ] High priority (this week)
- [ ] Medium priority (next week)

### 8. Looking Ahead
- Scheduled tasks
- Expected communications
- Planned activities

## Data Sources
1. `AI_Employee_Vault/Logs/*.json` - Activity logs
2. `AI_Employee_Vault/Audit/*.json` - Audit trail
3. `AI_Employee_Vault/Done/` - Completed tasks
4. `AI_Employee_Vault/Needs_Action/` - Pending tasks
5. API endpoints: `/api/audit/stats`, `/api/ralph/status`

## Formatting Guidelines
- Use markdown formatting
- Include date range at top
- Keep executive summary under 200 words
- Use tables for metrics where appropriate
- Include trend indicators (up/down arrows)

## Sample Output Structure

```markdown
# CEO Briefing
**Period:** January 22-28, 2026
**Generated:** January 29, 2026

## Executive Summary
[One paragraph overview...]

## Communication Metrics

### Email
| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| Received | 45 | 38 | +18% |
| Sent | 32 | 28 | +14% |
| Response Rate | 95% | 92% | +3% |

### WhatsApp
[Similar table...]

### LinkedIn
[Similar table...]

## Task Pipeline
- **Inbox:** 3 items
- **In Progress:** 5 items
- **Completed:** 12 items
- **Blocked:** 1 item (requires external input)

## Ralph Wiggum Performance
- Tasks processed: 8
- Success rate: 87.5%
- Avg steps/task: 4.2

## Audit Summary
- Total events: 156
- Errors: 2
- Warnings: 5
- All platforms healthy

## Action Items
- [ ] **CRITICAL:** Review blocked task #123
- [ ] Review pending approvals (2 items)
- [ ] Schedule Q1 planning meeting

## Looking Ahead
- Monday: Weekly team sync
- Wednesday: Quarterly review prep
- Friday: Report deadline
```

## Constraints
- Only use data from the vault
- Do not make up or estimate missing data
- Mark any incomplete sections with "[Data not available]"
- Include confidence indicators where appropriate
