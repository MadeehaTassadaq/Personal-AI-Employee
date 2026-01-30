"""Unified Social Media API endpoints.

Provides a single interface to query all social media platforms
for dashboard integration and CEO briefings.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class PlatformStatus(BaseModel):
    """Status of a social media platform."""
    platform: str
    status: str  # connected, error, not_configured
    error: Optional[str] = None
    last_check: str


class SocialStats(BaseModel):
    """Aggregated social media statistics."""
    platform: str
    followers: Optional[int] = None
    posts_count: Optional[int] = None
    engagement: Optional[Dict[str, Any]] = None
    recent_activity: Optional[str] = None


async def check_platform_status(platform: str) -> PlatformStatus:
    """Check the status of a social media platform."""
    now = datetime.now().isoformat()

    # Check environment variables for each platform
    platform_configs = {
        "facebook": ["FACEBOOK_PAGE_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"],
        "instagram": ["FACEBOOK_PAGE_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"],
        "twitter": ["TWITTER_BEARER_TOKEN"],
        "linkedin": ["LINKEDIN_ACCESS_TOKEN"]
    }

    required_vars = platform_configs.get(platform, [])

    # Check if all required vars are set
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        return PlatformStatus(
            platform=platform,
            status="not_configured",
            error=f"Missing: {', '.join(missing)}",
            last_check=now
        )

    # For now, just check configuration
    # In production, would actually test API connection
    return PlatformStatus(
        platform=platform,
        status="configured",
        last_check=now
    )


@router.get("/status")
async def get_all_platform_status():
    """Get status of all social media platforms.

    Returns:
        Status of each configured platform
    """
    platforms = ["facebook", "instagram", "twitter", "linkedin"]

    statuses = []
    for platform in platforms:
        status = await check_platform_status(platform)
        statuses.append(status.model_dump())

    # Count connected vs not
    connected = sum(1 for s in statuses if s["status"] == "configured")
    total = len(platforms)

    return {
        "platforms": statuses,
        "summary": {
            "configured": connected,
            "total": total
        },
        "checked_at": datetime.now().isoformat()
    }


@router.get("/status/{platform}")
async def get_platform_status(platform: str):
    """Get status of a specific platform.

    Args:
        platform: Platform name (facebook, instagram, twitter, linkedin)

    Returns:
        Platform status
    """
    valid_platforms = ["facebook", "instagram", "twitter", "linkedin"]

    if platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
        )

    status = await check_platform_status(platform)
    return status.model_dump()


@router.get("/stats")
async def get_aggregated_stats():
    """Get aggregated statistics from all platforms.

    Note: In production, this would call each MCP server to get real stats.
    Currently returns mock data for demonstration.

    Returns:
        Aggregated social media statistics
    """
    # Check which platforms are configured
    platforms_status = []
    for platform in ["facebook", "instagram", "twitter", "linkedin"]:
        status = await check_platform_status(platform)
        platforms_status.append((platform, status.status))

    stats = []

    for platform, status in platforms_status:
        if status == "configured":
            # In production, would call MCP tools here
            # For now, return placeholder indicating it needs real data
            stats.append({
                "platform": platform,
                "status": "configured",
                "message": "Connect to MCP server for real stats",
                "followers": None,
                "engagement": None
            })
        else:
            stats.append({
                "platform": platform,
                "status": "not_configured",
                "message": "Platform not configured"
            })

    return {
        "stats": stats,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/engagement")
async def get_engagement_summary():
    """Get engagement summary across all platforms.

    Returns:
        Engagement metrics for CEO briefing
    """
    # This would aggregate real data from each platform
    # For now, returns structure for integration

    return {
        "summary": {
            "total_followers": None,
            "total_posts_this_week": None,
            "total_engagement": None,
            "top_platform": None
        },
        "platforms": {
            "facebook": {
                "configured": bool(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")),
                "page_likes": None,
                "reach": None,
                "engagement_rate": None
            },
            "instagram": {
                "configured": bool(os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")),
                "followers": None,
                "impressions": None,
                "engagement_rate": None
            },
            "twitter": {
                "configured": bool(os.getenv("TWITTER_BEARER_TOKEN")),
                "followers": None,
                "tweet_impressions": None,
                "engagement_rate": None
            },
            "linkedin": {
                "configured": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
                "connections": None,
                "post_impressions": None,
                "engagement_rate": None
            }
        },
        "note": "Configure MCP servers and set DRY_RUN=false for real data",
        "generated_at": datetime.now().isoformat()
    }


@router.get("/recent-posts")
async def get_recent_posts(limit: int = 10):
    """Get recent posts across all configured platforms.

    Args:
        limit: Maximum posts per platform

    Returns:
        Recent posts from each platform
    """
    posts = {
        "facebook": [],
        "instagram": [],
        "twitter": [],
        "linkedin": []
    }

    # In production, would call each MCP server
    # For now, indicate which platforms are ready for data

    for platform in posts.keys():
        status = await check_platform_status(platform)
        if status.status == "configured":
            posts[platform] = [{
                "message": f"{platform.title()} MCP server ready",
                "note": "Call MCP tool for real posts"
            }]
        else:
            posts[platform] = [{
                "message": f"{platform.title()} not configured",
                "note": status.error
            }]

    return {
        "posts": posts,
        "limit": limit,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/health")
async def social_health_check():
    """Health check for social media integrations.

    Returns:
        Overall health status
    """
    platforms = ["facebook", "instagram", "twitter", "linkedin"]
    health = {}

    for platform in platforms:
        status = await check_platform_status(platform)
        health[platform] = {
            "healthy": status.status == "configured",
            "status": status.status,
            "error": status.error
        }

    healthy_count = sum(1 for h in health.values() if h["healthy"])

    return {
        "overall": "healthy" if healthy_count > 0 else "degraded",
        "platforms": health,
        "configured_count": healthy_count,
        "total_count": len(platforms),
        "checked_at": datetime.now().isoformat()
    }
