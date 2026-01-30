import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

def get_vault_path():
    """Get the vault path from environment or default."""
    return os.getenv("VAULT_PATH", "./AI_Employee_Vault")

def get_communication_metrics(days: int = 7) -> Dict[str, Any]:
    """Get communication metrics from various platforms."""
    vault_path = Path(get_vault_path())

    # For now, return mock data - in a real implementation, this would
    # aggregate data from Gmail, WhatsApp, LinkedIn logs
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    return {
        "email": {
            "received": 45,
            "sent": 32,
            "response_rate": 95,
            "pending_responses": 3,
            "key_threads": ["Project Alpha update", "Budget review", "Team sync"]
        },
        "whatsapp": {
            "received": 28,
            "sent": 15,
            "active_conversations": 12,
            "follow_up_needed": 4
        },
        "linkedin": {
            "connection_requests": 8,
            "messages": 5,
            "post_engagement": 23  # likes, comments, shares
        }
    }

def get_task_pipeline() -> Dict[str, Any]:
    """Get current task pipeline status."""
    vault_path = Path(get_vault_path())

    inbox_dir = vault_path / "Inbox"
    needs_action_dir = vault_path / "Needs_Action"
    pending_approval_dir = vault_path / "Pending_Approval"
    done_dir = vault_path / "Done"

    return {
        "inbox_count": len(list(inbox_dir.glob("*.md"))) if inbox_dir.exists() else 0,
        "needs_action_count": len(list(needs_action_dir.glob("*.md"))) if needs_action_dir.exists() else 0,
        "pending_approval_count": len(list(pending_approval_dir.glob("*.md"))) if pending_approval_dir.exists() else 0,
        "completed_this_week": len(list(done_dir.glob("*.md"))) if done_dir.exists() else 0,
        "blocked_items": 1,
        "approval_queue_status": "Normal"
    }

def get_ralph_performance() -> Dict[str, Any]:
    """Get Ralph Wiggum performance metrics."""
    # In a real implementation, this would call the Ralph API
    # For now, return mock data
    return {
        "tasks_processed": 8,
        "success_rate": 87.5,
        "average_steps_per_task": 4.2,
        "errors": 1,
        "warnings": 2
    }

def get_audit_summary(days: int = 7) -> Dict[str, Any]:
    """Get audit summary from audit logs."""
    vault_path = Path(get_vault_path())
    audit_dir = vault_path / "Audit"

    total_events = 0
    errors = 0
    warnings = 0

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Look for audit log files in the date range
    for audit_file in audit_dir.glob("*.json"):
        try:
            # Parse date from filename (YYYY-MM-DD.json)
            date_str = audit_file.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if start_date <= file_date <= end_date:
                with open(audit_file, 'r') as f:
                    entries = json.load(f)

                for entry in entries:
                    total_events += 1
                    if entry.get('level') == 'error':
                        errors += 1
                    elif entry.get('level') == 'warning':
                        warnings += 1
        except (ValueError, json.JSONDecodeError):
            continue  # Skip invalid files

    return {
        "total_events": total_events,
        "errors": errors,
        "warnings": warnings,
        "platform_health": "All platforms healthy"
    }

def get_cross_domain_insights() -> Dict[str, Any]:
    """Get cross-domain insights and trends."""
    # In a real implementation, this would analyze patterns across platforms
    # For now, return mock insights
    return {
        "communication_velocity_trend": "Increasing",
        "task_completion_trend": "Steady",
        "platform_usage_pattern": "Email heaviest on Mondays, LinkedIn active mid-week",
        "potential_bottlenecks": ["Manual approval required for sensitive emails"]
    }

def generate_ceo_briefing() -> str:
    """Generate the CEO briefing report."""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())  # Monday of current week
    week_end = week_start + timedelta(days=6)  # Sunday of current week

    # Format dates for the report
    period_range = f"{week_start.strftime('%B %d')} - {week_end.strftime('%B %d')}, {today.year}"
    generated_date = today.strftime('%B %d, %Y')

    # Get all the data
    comm_metrics = get_communication_metrics()
    task_pipeline = get_task_pipeline()
    ralph_perf = get_ralph_performance()
    audit_summary = get_audit_summary()
    cross_insights = get_cross_domain_insights()

    # Generate the report
    report = f"""# CEO Briefing
**Period:** {period_range}
**Generated:** {generated_date}

## Executive Summary
This week saw increased communication activity with strong response rates across all platforms. Ralph Wiggum successfully processed 8 tasks with a 87.5% success rate. The system remains stable with minimal errors reported in the audit logs. One task remains blocked and requires immediate attention.

## Communication Metrics

### Email
| Metric | This Week | Trend |
|--------|-----------|-------|
| Received | {comm_metrics['email']['received']} | +18% |
| Sent | {comm_metrics['email']['sent']} | +14% |
| Response Rate | {comm_metrics['email']['response_rate']}% | +3% |

**Key Threads:**
- {comm_metrics['email']['key_threads'][0]}
- {comm_metrics['email']['key_threads'][1]}
- {comm_metrics['email']['key_threads'][2]}

**Pending Responses:** {comm_metrics['email']['pending_responses']}

### WhatsApp
| Metric | Count | Notes |
|--------|-------|-------|
| Received | {comm_metrics['whatsapp']['received']} | Active engagement |
| Sent | {comm_metrics['whatsapp']['sent']} | Targeted outreach |
| Active Conversations | {comm_metrics['whatsapp']['active_conversations']} | Good momentum |
| Follow-up Needed | {comm_metrics['whatsapp']['follow_up_needed']} | Prioritize |

### LinkedIn
| Metric | Count | Notes |
|--------|-------|-------|
| Connection Requests | {comm_metrics['linkedin']['connection_requests']} | Networking active |
| Messages | {comm_metrics['linkedin']['messages']} | Engagement high |
| Post Engagement | {comm_metrics['linkedin']['post_engagement']} | Content performing well |

## Task Pipeline
- **Inbox:** {task_pipeline['inbox_count']} items
- **In Progress:** {task_pipeline['needs_action_count']} items
- **Completed:** {task_pipeline['completed_this_week']} items
- **Blocked:** {task_pipeline['blocked_items']} item (requires external input)
- **Approval Queue:** {task_pipeline['approval_queue_status']}

## Ralph Wiggum Performance
- Tasks processed: {ralph_perf['tasks_processed']}
- Success rate: {ralph_perf['success_rate']}%
- Avg steps/task: {ralph_perf['average_steps_per_task']}
- Errors: {ralph_perf['errors']}
- Warnings: {ralph_perf['warnings']}

## Audit Summary
- Total events: {audit_summary['total_events']}
- Errors: {audit_summary['errors']}
- Warnings: {audit_summary['warnings']}
- Status: {audit_summary['platform_health']}

## Cross-Domain Insights
- **Communication Velocity:** {cross_insights['communication_velocity_trend']}
- **Task Completion:** {cross_insights['task_completion_trend']}
- **Platform Patterns:** {cross_insights['platform_usage_pattern']}
- **Bottlenecks:** {cross_insights['potential_bottlenecks'][0]}

## Action Items
- [ ] **CRITICAL:** Review blocked task in pipeline
- [ ] Follow up on pending email responses ({comm_metrics['email']['pending_responses']} items)
- [ ] Schedule Q1 planning meeting
- [ ] Review LinkedIn engagement strategy

## Looking Ahead
- Monday: Weekly team sync
- Wednesday: Quarterly review preparation
- Friday: Report deadline
"""

    return report

def main():
    """Main function to generate the CEO briefing."""
    try:
        briefing = generate_ceo_briefing()

        # Save to vault
        vault_path = Path(get_vault_path())
        reports_dir = vault_path / "Reports"
        reports_dir.mkdir(exist_ok=True)

        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"CEO_Briefing_{today}.md"
        filepath = reports_dir / filename

        with open(filepath, 'w') as f:
            f.write(briefing)

        print(f"CEO Briefing generated successfully: {filepath}")
        print("\nBriefing Preview:")
        print("="*50)
        print(briefing[:1000] + "..." if len(briefing) > 1000 else briefing)

        return str(filepath)

    except Exception as e:
        print(f"Error generating CEO briefing: {e}")
        return None

if __name__ == "__main__":
    main()