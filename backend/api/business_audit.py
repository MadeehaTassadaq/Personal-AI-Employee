"""Business Audit API endpoints."""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Any

from fastapi import APIRouter, HTTPException
import yaml

from ..services.audit_logger import get_audit_logger, AuditAction, AuditLevel

router = APIRouter()


class BusinessAuditGenerator:
    """Generates comprehensive business audit reports."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path

    def _parse_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                return yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                return {}
        return {}

    def check_platform_health(self) -> dict:
        """Check health status of all platform integrations."""
        platforms = {
            "gmail": {
                "configured": bool(os.getenv("GMAIL_CREDENTIALS_PATH")),
                "status": "unknown",
                "last_activity": None
            },
            "whatsapp": {
                "configured": bool(os.getenv("WHATSAPP_SESSION_PATH")),
                "status": "unknown",
                "last_activity": None
            },
            "linkedin": {
                "configured": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
                "status": "unknown",
                "last_activity": None
            },
            "facebook": {
                "configured": bool(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")),
                "status": "unknown",
                "last_activity": None
            },
            "instagram": {
                "configured": bool(os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")),
                "status": "unknown",
                "last_activity": None
            },
            "twitter": {
                "configured": bool(os.getenv("TWITTER_API_KEY")),
                "status": "unknown",
                "last_activity": None
            },
            "calendar": {
                "configured": bool(os.getenv("CALENDAR_CREDENTIALS_PATH")),
                "status": "unknown",
                "last_activity": None
            }
        }

        # Check logs for recent activity
        logs_path = self.vault_path / "Logs"
        if logs_path.exists():
            log_files = sorted(logs_path.glob("*.json"), reverse=True)
            for log_file in log_files[:7]:  # Last 7 days
                try:
                    entries = json.loads(log_file.read_text())
                    if not isinstance(entries, list):
                        entries = [entries]

                    for entry in entries:
                        platform = entry.get("platform", "").lower()
                        if platform in platforms:
                            if platforms[platform]["last_activity"] is None:
                                platforms[platform]["last_activity"] = entry.get("timestamp")
                                platforms[platform]["status"] = "active"
                except (json.JSONDecodeError, KeyError):
                    continue

        # Set status based on configuration and activity
        for name, info in platforms.items():
            if not info["configured"]:
                info["status"] = "not_configured"
            elif info["last_activity"] is None:
                info["status"] = "idle"

        return platforms

    def get_social_metrics(self) -> dict:
        """Aggregate social media metrics from logs."""
        metrics = {
            "total_posts": 0,
            "by_platform": {
                "linkedin": {"posts": 0, "engagement": 0},
                "facebook": {"posts": 0, "engagement": 0},
                "instagram": {"posts": 0, "engagement": 0},
                "twitter": {"posts": 0, "engagement": 0}
            },
            "communications": {
                "emails_sent": 0,
                "whatsapp_messages": 0
            },
            "period": "last_7_days"
        }

        logs_path = self.vault_path / "Logs"
        if not logs_path.exists():
            return metrics

        log_files = list(logs_path.glob("*.json"))
        for log_file in log_files[-7:]:
            try:
                entries = json.loads(log_file.read_text())
                if not isinstance(entries, list):
                    entries = [entries]

                for entry in entries:
                    platform = entry.get("platform", "").lower()
                    action = entry.get("action", entry.get("action_type", "")).lower()

                    if platform == "linkedin" and "post" in action:
                        metrics["by_platform"]["linkedin"]["posts"] += 1
                        metrics["total_posts"] += 1
                    elif platform == "facebook" and "post" in action:
                        metrics["by_platform"]["facebook"]["posts"] += 1
                        metrics["total_posts"] += 1
                    elif platform == "instagram" and "post" in action:
                        metrics["by_platform"]["instagram"]["posts"] += 1
                        metrics["total_posts"] += 1
                    elif platform == "twitter" and ("post" in action or "tweet" in action):
                        metrics["by_platform"]["twitter"]["posts"] += 1
                        metrics["total_posts"] += 1
                    elif platform == "email" or "email" in action:
                        metrics["communications"]["emails_sent"] += 1
                    elif platform == "whatsapp" or "whatsapp" in action:
                        metrics["communications"]["whatsapp_messages"] += 1
            except (json.JSONDecodeError, KeyError):
                continue

        return metrics

    def get_task_analytics(self) -> dict:
        """Analyze task completion rates and patterns."""
        analytics = {
            "total_tasks": 0,
            "completed_this_week": 0,
            "pending_approval": 0,
            "in_progress": 0,
            "inbox": 0,
            "completion_rate": 0.0,
            "avg_completion_time_hours": None,
            "bottlenecks": []
        }

        # Count by folder
        folders = {
            "Inbox": "inbox",
            "Needs_Action": "in_progress",
            "Pending_Approval": "pending_approval",
            "Done": "completed_this_week"
        }

        for folder, key in folders.items():
            folder_path = self.vault_path / folder
            if folder_path.exists():
                count = len([f for f in folder_path.glob("*.md") if not f.name.startswith(".")])
                analytics[key] = count
                analytics["total_tasks"] += count

        # Calculate completion rate
        if analytics["total_tasks"] > 0:
            analytics["completion_rate"] = round(
                (analytics["completed_this_week"] / analytics["total_tasks"]) * 100, 1
            )

        # Identify bottlenecks
        if analytics["pending_approval"] > 10:
            analytics["bottlenecks"].append({
                "type": "approval_backlog",
                "count": analytics["pending_approval"],
                "recommendation": "Review and clear pending approvals"
            })

        if analytics["in_progress"] > 20:
            analytics["bottlenecks"].append({
                "type": "task_overload",
                "count": analytics["in_progress"],
                "recommendation": "Consider pausing new task intake"
            })

        if analytics["inbox"] > 15:
            analytics["bottlenecks"].append({
                "type": "inbox_overflow",
                "count": analytics["inbox"],
                "recommendation": "Process inbox items"
            })

        return analytics

    def get_financial_summary(self) -> dict:
        """Get financial summary from Odoo (if configured)."""
        odoo_url = os.getenv("ODOO_URL")

        if not odoo_url:
            return {
                "status": "not_configured",
                "message": "Odoo integration not configured. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD in .env",
                "data": None
            }

        # Placeholder for Odoo integration
        # In full implementation, this would call Odoo APIs
        return {
            "status": "configured",
            "message": "Odoo configured but not connected",
            "data": {
                "revenue_mtd": None,
                "expenses_mtd": None,
                "outstanding_invoices": None,
                "last_sync": None
            }
        }

    def check_alert_thresholds(self) -> list:
        """Check business goals alert thresholds."""
        alerts = []
        analytics = self.get_task_analytics()

        # Critical alerts
        if analytics["pending_approval"] > 20:
            alerts.append({
                "level": "critical",
                "type": "approval_backlog",
                "message": f"{analytics['pending_approval']} items pending approval (threshold: 20)",
                "recommendation": "Pause new task intake and clear approvals"
            })

        # Check for stale approvals
        pending_path = self.vault_path / "Pending_Approval"
        if pending_path.exists():
            stale_count = 0
            for file_path in pending_path.glob("*.md"):
                if file_path.name.startswith("."):
                    continue
                age_hours = (datetime.now().timestamp() - file_path.stat().st_mtime) / 3600
                if age_hours > 48:
                    stale_count += 1

            if stale_count > 0:
                alerts.append({
                    "level": "warning",
                    "type": "stale_approvals",
                    "message": f"{stale_count} approvals older than 48 hours",
                    "recommendation": "Review and process stale approval items"
                })

        # Check weekly task completion
        if analytics["completed_this_week"] < 30:
            alerts.append({
                "level": "warning",
                "type": "low_throughput",
                "message": f"Only {analytics['completed_this_week']} tasks completed this week (target: 30+)",
                "recommendation": "Check if Ralph Wiggum is running and watchers are active"
            })

        # Check social media activity
        social_metrics = self.get_social_metrics()
        if social_metrics["total_posts"] < 5:
            alerts.append({
                "level": "info",
                "type": "low_social_activity",
                "message": f"Only {social_metrics['total_posts']} social posts this week (target: 7+)",
                "recommendation": "Review content calendar and watcher status"
            })

        return alerts

    def generate_audit_report(self) -> str:
        """Generate comprehensive audit report."""
        now = datetime.now()

        platform_health = self.check_platform_health()
        social_metrics = self.get_social_metrics()
        task_analytics = self.get_task_analytics()
        financial_summary = self.get_financial_summary()
        alerts = self.check_alert_thresholds()

        # Build report
        report = f"""---
type: business_audit
created: {now.isoformat()}
---

# Business Audit Report

**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

This audit covers platform integrations, social media performance, task completion rates, and financial status.

**Key Findings:**
- **Platforms Configured:** {sum(1 for p in platform_health.values() if p['configured'])} / {len(platform_health)}
- **Total Social Posts (7 days):** {social_metrics['total_posts']}
- **Task Completion Rate:** {task_analytics['completion_rate']}%
- **Active Alerts:** {len(alerts)}

---

## Platform Health Status

| Platform | Configured | Status | Last Activity |
|----------|------------|--------|---------------|
"""

        for name, info in platform_health.items():
            configured = "✅" if info["configured"] else "❌"
            status_icon = {"active": "🟢", "idle": "🟡", "not_configured": "⚪", "unknown": "🔴"}.get(info["status"], "⚪")
            last_activity = info["last_activity"][:10] if info["last_activity"] else "N/A"
            report += f"| {name.title()} | {configured} | {status_icon} {info['status']} | {last_activity} |\n"

        report += """
---

## Social Media Performance

"""

        report += f"""### Posts by Platform (Last 7 Days)

| Platform | Posts | Status |
|----------|-------|--------|
| LinkedIn | {social_metrics['by_platform']['linkedin']['posts']} | {'✅' if social_metrics['by_platform']['linkedin']['posts'] >= 2 else '⚠️'} |
| Facebook | {social_metrics['by_platform']['facebook']['posts']} | {'✅' if social_metrics['by_platform']['facebook']['posts'] >= 1 else '⚠️'} |
| Instagram | {social_metrics['by_platform']['instagram']['posts']} | {'✅' if social_metrics['by_platform']['instagram']['posts'] >= 1 else '⚠️'} |
| Twitter/X | {social_metrics['by_platform']['twitter']['posts']} | {'✅' if social_metrics['by_platform']['twitter']['posts'] >= 2 else '⚠️'} |
| **Total** | **{social_metrics['total_posts']}** | |

### Communications

| Channel | Count |
|---------|-------|
| Emails Sent | {social_metrics['communications']['emails_sent']} |
| WhatsApp Messages | {social_metrics['communications']['whatsapp_messages']} |

---

## Task Analytics

| Metric | Value | Target |
|--------|-------|--------|
| Total Tasks | {task_analytics['total_tasks']} | — |
| Completed This Week | {task_analytics['completed_this_week']} | 50+ |
| Pending Approval | {task_analytics['pending_approval']} | < 5 |
| In Progress | {task_analytics['in_progress']} | — |
| Inbox | {task_analytics['inbox']} | < 10 |
| Completion Rate | {task_analytics['completion_rate']}% | > 80% |

"""

        if task_analytics["bottlenecks"]:
            report += "### Bottlenecks Identified\n\n"
            for b in task_analytics["bottlenecks"]:
                report += f"- **{b['type']}:** {b['count']} items — {b['recommendation']}\n"

        report += """
---

## Financial Summary

"""

        if financial_summary["status"] == "not_configured":
            report += f"_{financial_summary['message']}_\n"
        else:
            report += f"""
| Metric | Value |
|--------|-------|
| Revenue MTD | {financial_summary['data'].get('revenue_mtd', 'N/A')} |
| Expenses MTD | {financial_summary['data'].get('expenses_mtd', 'N/A')} |
| Outstanding Invoices | {financial_summary['data'].get('outstanding_invoices', 'N/A')} |
"""

        report += """
---

## Alerts & Recommendations

"""

        if alerts:
            for alert in alerts:
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert["level"], "⚪")
                report += f"### {icon} {alert['type'].replace('_', ' ').title()}\n\n"
                report += f"**Level:** {alert['level'].upper()}\n\n"
                report += f"**Message:** {alert['message']}\n\n"
                report += f"**Recommendation:** {alert['recommendation']}\n\n"
        else:
            report += "✅ _No alerts at this time._\n"

        report += """
---

## Action Items

"""

        # Generate action items based on findings
        actions = []

        unconfigured = [name for name, info in platform_health.items() if not info["configured"]]
        if unconfigured:
            actions.append(f"Configure platform credentials: {', '.join(unconfigured)}")

        if task_analytics["pending_approval"] > 5:
            actions.append(f"Clear {task_analytics['pending_approval']} pending approvals")

        if social_metrics["total_posts"] < 7:
            actions.append("Create and schedule more social media content")

        if actions:
            for i, action in enumerate(actions, 1):
                report += f"{i}. {action}\n"
        else:
            report += "_No immediate actions required._\n"

        report += """
---

*This audit was automatically generated by your Personal AI Employee.*
"""

        return report

    def save_audit(self, content: str) -> str:
        """Save audit to Reports folder."""
        reports_path = self.vault_path / "Reports"
        reports_path.mkdir(parents=True, exist_ok=True)

        filename = f"Business_Audit_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.md"
        file_path = reports_path / filename

        file_path.write_text(content)

        return str(file_path)


@router.post("/generate")
async def generate_business_audit():
    """Generate a comprehensive business audit report.

    Returns:
        Path to the generated audit file and summary data
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))

        generator = BusinessAuditGenerator(vault_path)
        audit_content = generator.generate_audit_report()
        report_path = generator.save_audit(audit_content)

        # Get summary data for response
        platform_health = generator.check_platform_health()
        task_analytics = generator.get_task_analytics()
        alerts = generator.check_alert_thresholds()

        # Log the action
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.INFO,
            platform="system",
            actor="business_audit",
            details={
                "action": "audit_generated",
                "report_path": report_path,
                "alert_count": len(alerts)
            }
        )

        return {
            "message": "Business audit generated successfully",
            "report_path": report_path,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "platforms_configured": sum(1 for p in platform_health.values() if p["configured"]),
                "total_platforms": len(platform_health),
                "task_completion_rate": task_analytics["completion_rate"],
                "pending_approvals": task_analytics["pending_approval"],
                "alert_count": len(alerts),
                "alerts": alerts
            }
        }

    except Exception as e:
        audit_logger = get_audit_logger()
        audit_logger.log(
            AuditAction.ERROR,
            platform="system",
            level=AuditLevel.ERROR,
            actor="business_audit",
            details={
                "action": "audit_generation_failed",
                "error": str(e)
            }
        )

        raise HTTPException(status_code=500, detail=f"Failed to generate audit: {str(e)}")


@router.get("/health")
async def get_platform_health():
    """Get current platform health status.

    Returns:
        Health status of all integrated platforms
    """
    vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
    generator = BusinessAuditGenerator(vault_path)

    return {
        "platforms": generator.check_platform_health(),
        "checked_at": datetime.now().isoformat()
    }


@router.get("/alerts")
async def get_active_alerts():
    """Get current active alerts based on business thresholds.

    Returns:
        List of active alerts
    """
    vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
    generator = BusinessAuditGenerator(vault_path)

    alerts = generator.check_alert_thresholds()

    return {
        "alerts": alerts,
        "count": len(alerts),
        "checked_at": datetime.now().isoformat()
    }


@router.get("/metrics")
async def get_business_metrics():
    """Get current business metrics summary.

    Returns:
        Task analytics and social media metrics
    """
    vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
    generator = BusinessAuditGenerator(vault_path)

    return {
        "tasks": generator.get_task_analytics(),
        "social_media": generator.get_social_metrics(),
        "financial": generator.get_financial_summary(),
        "retrieved_at": datetime.now().isoformat()
    }


@router.get("/latest")
async def get_latest_audit():
    """Get the most recent business audit report.

    Returns:
        Content of the latest audit report
    """
    vault_path = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))
    reports_dir = vault_path / "Reports"

    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="No reports directory found")

    audit_files = list(reports_dir.glob("Business_Audit_*.md"))

    if not audit_files:
        raise HTTPException(status_code=404, detail="No business audits found")

    latest_file = max(audit_files, key=lambda f: f.stat().st_mtime)

    try:
        content = latest_file.read_text()

        return {
            "file_path": str(latest_file),
            "content": content,
            "modified_at": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read audit: {str(e)}")
