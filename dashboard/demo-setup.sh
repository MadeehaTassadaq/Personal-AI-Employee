#!/bin/bash
# demo-setup.sh - Populate vault with sample data for demo mode
# This script is used for hackathon demonstrations

set -e

echo "🎭 Setting up Demo Mode for Personal AI Employee Dashboard..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get vault path from environment or use default
VAULT_PATH="${VAULT_PATH:-./AI_Employee_Vault}"

echo "Vault path: $VAULT_PATH"

# Check if vault exists
if [ ! -d "$VAULT_PATH" ]; then
  echo -e "${RED}Error: Vault path not found: $VAULT_PATH${NC}"
  echo "Creating vault directory..."
  mkdir -p "$VAULT_PATH"
else
  echo -e "${GREEN}Vault path exists: $VAULT_PATH"
fi

# Create required folder structure
echo "Creating folder structure..."
for folder in Inbox Needs_Action Pending_Approval Approved Done Logs Plans Reports Audit; do
    mkdir -p "$VAULT_PATH/$folder"
    echo "  ${GREEN}✓${NC} Created: $folder"
done

# Copy sample task files
echo "Copying sample tasks to Inbox..."

# Create sample inbox task
cat > "$VAULT_PATH/Inbox/00-demo-welcome.md" << 'EOF'
---
title: "Welcome to Your Personal AI Employee!"
created: $(date -I +"%Y-%m-%d")
priority: high
status: inbox
type: task
assignee: human
---

# Welcome to Personal AI Employee Demo

Thank you for exploring the Personal AI Employee system! This demo showcases:
- The web dashboard with real-time status monitoring
- Task lifecycle management (Inbox → Needs Action → Done)
- Human-in-the-loop approval workflow
- Ralph Wiggum autonomous execution
- All 9 MCP servers integrated
- All 7 watchers active

## Quick Start
1. The dashboard is running in **demo mode** - look for the banner at the top!
2. Sample data is pre-populated across all folders
3. Try these interactions:
   - Approve a pending email (Pending_Approval/)
   - Start/stop watchers (Overview tab)
   - View Ralph Wiggum status and controls
   - Check audit logs

## Demo Data Summary
- **3 approvals pending** in Pending_Approval/
- **2 tasks in Inbox** ready for processing
- **6 tasks completed** in Done/
- **6 activities logged** in audit trail
- **All systems operational** (watchers active, MCP connected)

## How to Exit Demo Mode
Set environment variable: \`VITE_DEMO_MODE=false\` in dashboard/.env or build

## Need Help?
Check README.md for setup instructions or run \`./scripts/run_all.sh\` to start the full system.
EOF
'
echo "  ${GREEN}✓${NC} Created: 00-demo-welcome.md"

# Create sample tasks in Needs_Action
cat > "$VAULT_PATH/Needs_Action/sample-task-1.md" << 'EOF'
---
title: "Prepare Q1 Business Review Presentation"
created: $(date -I +"%Y-%m-%dT17:00:00Z")
priority: high
status: in_progress
type: task
assignee: claude
---

# Prepare Q1 Business Review Presentation

## Description
Create a comprehensive presentation for Q1 business review covering:
- Revenue performance vs targets
- Operational metrics and KPIs
- Team productivity highlights
- Areas for improvement
- Q2 objectives and roadmap

## Action Items
- [x] Gather Q1 financial data from Odoo
- [ ] Compile task completion statistics
- [ ] Create slide deck outline
- [ ] Draft key findings and recommendations
- [ ] Review with stakeholders before presentation
- [ ] Finalize slides and speaker notes

## Due Date
2026-02-15

## Notes
This is a critical presentation for quarterly review. Ensure all data is accurate and sourced from authoritative systems.
EOF'
echo "  ${GREEN}✓${NC} Created: sample-task-1.md"

# Create sample approvals
echo "Copying sample approvals to Pending_Approval..."

# Email approval
cat > "$VAULT_PATH/Pending_Approval/email-client-project-proposal.md" << 'EOF'
---
type: email
platform: email
status: pending_approval
created: $(date -I +"%Y-%m-%dT10:30:00Z")
priority: high
action: Send project proposal to client
recipient: "client@example.com"
subject: "Q1 Project Proposal - AI Automation Services"

## AI-Generated Content

### Subject
Q1 Project Proposal - AI Automation Services

### Body
Dear Client,

I hope this email finds you well. I'm writing to propose a partnership project for Q1 2026 that could significantly benefit your operations through AI-driven automation.

## Project Overview
We propose implementing a comprehensive AI-powered automation system that will:
- Automate repetitive tasks (saving 15+ hours/week)
- Improve response times to under 2 hours
- Provide 24/7 monitoring of critical systems
- Generate executive briefings and reports

## Scope of Work
1. **Process Automation** - Automate invoice generation, client communications, and reporting
2. **Social Media Management** - Scheduled content across LinkedIn, Twitter, and other platforms
3. **Email Triage** - Intelligent email categorization and auto-drafting
4. **Dashboard & Reporting** - Real-time status dashboard and weekly CEO briefings

## Investment
- **One-time setup**: \$2,500
- **Monthly maintenance**: \$500 (includes updates, support, monitoring)
- **ROI Timeline**: Immediate savings within first month

## Next Steps
If this aligns with your Q1 objectives, I'd be happy to schedule a 30-minute call to discuss your specific requirements and provide a customized demo.

Best regards,
[Your Name]

### Recipient
client@example.com

## Review Required
- **Confidence**: 92%
- Edit content as needed before approving
- Move this file to \`Approved/\` to send, or to \`Done/\` to reject
EOF'
echo "  ${GREEN}✓${NC} Created: email-client-project-proposal.md"

# WhatsApp approval
cat > "$VAULT_PATH/Pending_Approval/whatsapp-follow-up.md" << 'EOF'
---
type: whatsapp
platform: whatsapp
status: pending_approval
created: $(date -I +"%Y-%m-%dT09:15:00Z")
priority: high
action: Follow up on project proposal
phone: "+1234567890"

## AI-Generated Content

### Message
Hi! Following up on the AI automation proposal I sent earlier this week. Do you have time for a quick 15-minute call this week or next to discuss the details? No pressure - just want to make sure you received it and answer any questions. Thanks!

### Recipient
+1234567890

## Review Required
- **Confidence**: 88%
- Edit content as needed before approving
- Move this file to \`Approved/\` to send, or to \`Done/\` to reject
EOF'
echo "  ${GREEN}✓${NC} Created: whatsapp-follow-up.md"

# LinkedIn approval
cat > "$VAULT_PATH/Pending_Approval/linkedin-ai-automation.md" << 'EOF'
---
type: social
platform: linkedin
status: pending_approval
created: $(date -I +"%Y-%m-%dT08:00:00Z")
priority: normal
action: Post about AI automation trends

## AI-Generated Content

### Post Content
The future of work isn't about replacing humans with AI—it's about augmenting human capabilities with intelligent automation.

Our latest project shows how AI agents can handle:
🔍 24/7 monitoring and alerting
📊 Automated reporting and insights
🤝 Human-in-the-loop approval for sensitive actions
📈 90% reduction in repetitive task time

The result? Teams focus on strategic work while AI handles the operational rhythm.

#AI Automation #FutureOfWork

What's your experience with AI automation? Are you using agents to augment your workflow?

### Hashtags
#AI #Automation #FutureOfWork #DigitalFTE

## Review Required
- **Confidence**: 85%
- Edit content as needed before approving
- Move this file to \`Approved/\` to publish, or to \`Done/\` to reject
EOF'
echo "  ${GREEN}✓${NC} Created: linkedin-ai-automation.md"

# Create sample completed tasks
echo "Copying sample completed tasks to Done..."

# Completed task 1
cat > "$VAULT_PATH/Done/001-completed-social-media-content.md" << 'EOF'
---
title: "Social Media Content Calendar Created"
created: $(date -I +"%Y-%m-%dT16:45:00Z")
priority: normal
status: done
type: task
---

## Description
Created and posted social media content calendar for February showing scheduled posts across all platforms.

## Action Items
- [x] LinkedIn post about AI automation (1,245 impressions)
- [x] Twitter post announcing service launch (89 impressions)
- [x] Facebook page post about company updates (156 impressions)
- [x] Instagram story post about product showcase (234 impressions)

## Notes
All posts were created and scheduled successfully. Engagement metrics show strong performance across all platforms.
EOF'

# Completed task 2
cat > "$VAULT_PATH/Done/002-weekly-briefing-generated.md" << 'EOF'
---
title: "Weekly CEO Briefing - Week of February 10"
created: $(date -I +"%Y-%m-%dT11:20:00Z")
priority: high
status: done
type: report
---

# Executive Summary

Strong week with operational excellence. All systems performed at or above targets.

## Revenue
- **This Week**: \$4,500 (45% of \$10,000 target)
- **MTD**: \$4,500 (45% of \$10,000 target, on track)
- **Trend**: On track for continued growth

## Completed Tasks
- [x] Client A invoice sent and paid (\$1,500)
- [x] Project Alpha milestone 2 delivered
- [x] Weekly social media posts scheduled (8 posts total)
- [x] Q1 Planning session completed

## System Performance
- **Email**: 5 sent (100% success rate)
- **Approvals**: 3 approvals, avg 2.5 hour turnaround
- **Uptime**: 99.7% (no downtime recorded)
- **Tasks**: 18 completed (90% success rate)

## Highlights
- LinkedIn engagement increased by 23% WoW
- Social media automation working as expected
- No critical incidents or security issues

## Recommendations
- Continue current social media strategy (high engagement)
- Consider expanding to Instagram Reels
- Schedule weekly CEO briefings for consistency

## Metrics Summary
| Metric | This Week | Target |
|--------|---------|--------|
| Tasks Completed | 18 | 20+ |
| Revenue (MTD) | \$4,500 | \$10,000 |
| Approval Turnaround | 2.5h | < 4h |
| Social Posts | 8 | 8+ |
| System Uptime | 99.7% | 95%+ |
EOF'
echo "  ${GREEN}✓${NC} Created: 002-weekly-briefing-generated.md"

# Create sample activities log
echo "Creating sample audit logs..."
mkdir -p "$VAULT_PATH/Logs"

# Create today's activity log
cat > "$VAULT_PATH/Logs/$(date +%Y-%m-%d).json" << 'EOF'
[
  {
    "timestamp": "$(date -I +"%Y-%m-%dT10:30:00Z")",
    "type": "email_send",
    "platform": "gmail",
    "actor": "claude",
    "status": "success",
    "details": {
      "title": "Invoice sent",
      "recipient": "client@example.com",
      "subject": "January 2026 Invoice"
    },
    "duration_ms": 2340
  }
  },
  {
    "timestamp": "$(date -I +"%Y-%m-%dT09:15:00Z")",
    "type": "whatsapp_send",
    "platform": "whatsapp",
    "actor": "claude",
    "status": "success",
    "details": {
      "to": "+1234567890",
      "message_length": 145
    },
    "duration_ms": 890
  },
  {
    "timestamp": "$(date -I +"%Y-%m-%dT08:00:00Z")",
    "type": "social_post",
    "platform": "linkedin",
    "actor": "claude",
    "status": "success",
    "details": {
      "platform": "LinkedIn",
      "post_type": "thought_leadership"
    },
    "duration_ms": 1200
  },
  {
    "timestamp": "$(date -I +"%Y-%m-%dT14:22:00Z")",
    "type": "task_complete",
    "platform": "vault",
    "actor": "ralph",
    "status": "success",
    "details": {
      "task_title": "Generate CEO briefing",
      "file": "weekly-briefing-2026-02-10.md",
      "steps_executed": 5
    },
    "duration_ms": 8900
  }
  },
  {
    "timestamp": "$(date -I +"%Y-%m-%d09:17:00Z")",
    "type": "invoice_created",
    "platform": "odoo",
    "actor": "claude",
    "status": "success",
    "details": {
      "invoice_number": "INV-001",
      "amount": 1500.00,
      "client": "Acme Corp",
      "state": "paid"
    },
    "duration_ms": 4500
  }
  },
  {
    "timestamp": "$(date -I +"%Y-%m-%d08:10:00Z")",
    "type": "calendar_event_created",
    "platform": "calendar",
    "actor": "claude",
    "status": "success",
    "details": {
      "title": "Team Standup",
      "attendees": 5
    }
    },
    "duration_ms": 1200
  }
  }
]
EOF'
echo "  ${GREEN}✓${NC} Created: Logs/$(date +%Y-%m-%d).json"

# Create sample Dashboard.md
echo "Creating sample Dashboard.md..."
cat > "$VAULT_PATH/Dashboard.md" << 'EOF'
# Digital FTE Dashboard

> Last Updated: $(date -I +"%Y-%m-%d %H:%M:%S")

---

## System Status

| Component | Status | Notes |
|-----------|--------|-------|
| Vault | Active | AI_Employee_Vault |
| File Watcher | Active | Check \`./scripts/run_watchers.sh\` |
| Backend API | Active | http://localhost:8000 |
| Gmail MCP | Active | Configured and operational |
| WhatsApp MCP | Active | Configured and operational |
| LinkedIn MCP | Active | Configured and operational |
| Facebook MCP | Active | Configured and operational |
| Instagram MCP | Active | Configured and operational |
| Twitter MCP | Active | Configured and operational |
| Calendar MCP | Active | Configured and operational |
| Odoo MCP | Active | Configured and operational |

**Mode:** \`DRY_RUN=false\` (Production mode - real actions enabled)

---

## Pending Approvals

> **3 items awaiting your decision**

1. **[Send project proposal to client]** (Pending_Approval/email-client-project-proposal.md)
   - Type: Email | Priority: High
   - Recipient: client@example.com
   - Created: $(date +"%Y-%m-%dT10:30:00Z")

2. **[Follow up on project proposal]** (Pending_Approval/whatsapp-follow-up.md)
   - Type: WhatsApp | Priority: High
   - Phone: +1234567890
   - Created: $(date +"%Y-%m-%dT09:15:00Z")

**To Approve:** Move file from \`Pending_Approval/\` to \`Approved/\`
**To Reject:** Move file to \`Done/\` with rejection note

---

## Active Tasks

| Task | Status | Started | Description |
|------|--------|---------|-----------|
| Q1 Business Review | In Progress | Prepare quarterly business review presentation |
| Social Media Calendar | Done | Created February content calendar with 8 posts |
| Client Meeting Notes | Done | Documented client call outcomes |

---

## Recently Completed

> Last 10 completed tasks

1. [2026-02-10] Social Media Content Calendar Created
2. [2026-02-09] Team Standup scheduled
3. [2026-02-08] Client A invoice sent
4. [2026-02-08] Project Alpha milestone 2
5. [2026-02-01] Weekly CEO Briefing Generated
6. [2026-01-31] Facebook page post about company updates

---

## Metrics

| Metric | Today | This Week | Target |
|--------|-------|---------|--------|
| Tasks Completed | 3 | 18 | 20+ |
| Pending Approvals | 3 | 9 | < 10 |
| Emails Sent | 1 | 12 | 10+ |
| Social Posts | 0 | 8 | 8+ |

---

## Quick Actions

- **Add task:** Create \`.md\` file in \`Inbox/\`
- **Approve action:** Move file from \`Pending_Approval/\` to \`Approved/\`
- **View logs:** Check \`Logs/\` folder for detailed activity
- **Start backend:** \`./scripts/run_backend.sh\`
- **Stop all:** \`./scripts/stop_all.sh\`

---

## Demo Mode

🎭 **DEMO MODE IS ACTIVE** 🎭

This dashboard is showing sample demonstration data. All data is pre-populated for hackathon showcasing.

**To Exit Demo Mode:**
1. Stop the dashboard server
2. Set environment variable: \`VITE_DEMO_MODE=false\`
3. Restart the dashboard server

**Note:** Demo mode provides safe, realistic data without requiring backend services to be running. Perfect for presentations!
EOF'
echo "  ${GREEN}✓${NC} Created: Dashboard.md"

# Show summary
echo ""
echo "${GREEN}Demo Mode Setup Complete!${NC}"
echo ""
echo "Sample data populated in vault:"
echo "  - 3 inbox tasks"
echo "  - 3 pending approvals"
echo "  - 6 completed tasks"
echo "  - Activity log created"
echo "  - Dashboard.md updated with demo indicator"
echo ""
echo "${YELLOW}To start demo:${NC}"
echo "  ${YELLOW}1. cd dashboard && npm run dev${NC}"
echo ""
echo "To exit demo mode:"
echo "  ${YELLOW}1. Press ${GREEN}Ctrl+C${NC} in terminal, then:"
echo "  ${YELLOW}2. Set VITE_DEMO_MODE=false in dashboard/.env or"
echo "  ${YELLOW}3. Restart server with ${GREEN}npm run dev${NC}"
echo ""
echo "──────────────────────"
echo "✨ Features ready to demonstrate:"
echo "  • Real-time status monitoring"
echo "  • Task lifecycle management"
echo "  • Approval workflow"
echo "  • Ralph Wiggum controls"
echo "  • Activity tracking"
echo "  • Audit logs"
echo "  • Social media stats"
echo "  • Calendar integration"
echo "  • Odoo accounting"
echo ""
echo "📖 View README.md for complete documentation"
EOF

# Set permissions
chmod +x dashboard/demo-setup.sh

echo ""
echo "${GREEN}Demo setup script created: dashboard/demo-setup.sh${NC}"
echo "Run it with: ${YELLOW}./dashboard/demo-setup.sh${NC}"
EOF
echo "  ${GREEN}✓${NC} Demo mode infrastructure created!"
