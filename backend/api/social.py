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

    Connects to MCP servers to get real data.

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
            try:
                # Attempt to import MCP modules dynamically to avoid startup errors
                if platform == "facebook":
                    try:
                        from mcp_services import mcp__facebook__get_page_info
                        page_info = await mcp__facebook__get_page_info()
                        stats.append({
                            "platform": platform,
                            "status": "configured",
                            "followers": page_info.get("fan_count", 0),
                            "engagement": {
                                "likes": page_info.get("likes", 0),
                                "talking_about_count": page_info.get("talking_about_count", 0)
                            }
                        })
                    except ImportError:
                        stats.append({
                            "platform": platform,
                            "status": "configured_no_mcp",
                            "message": "MCP server not available",
                            "followers": None,
                            "engagement": None
                        })
                elif platform == "instagram":
                    try:
                        from mcp_services import mcp__instagram__get_account_info
                        account_info = await mcp__instagram__get_account_info()
                        stats.append({
                            "platform": platform,
                            "status": "configured",
                            "followers": account_info.get("followers_count", 0),
                            "engagement": {
                                "following": account_info.get("follows_count", 0),
                                "media_count": account_info.get("media_count", 0)
                            }
                        })
                    except ImportError:
                        stats.append({
                            "platform": platform,
                            "status": "configured_no_mcp",
                            "message": "MCP server not available",
                            "followers": None,
                            "engagement": None
                        })
                elif platform == "linkedin":
                    try:
                        from mcp_services import mcp__linkedin__get_profile
                        profile_info = await mcp__linkedin__get_profile()
                        stats.append({
                            "platform": platform,
                            "status": "configured",
                            "followers": profile_info.get("connections", 0),
                            "engagement": {
                                "impressions": profile_info.get("impressions", 0),
                                "clicks": profile_info.get("clicks", 0)
                            }
                        })
                    except ImportError:
                        stats.append({
                            "platform": platform,
                            "status": "configured_no_mcp",
                            "message": "MCP server not available",
                            "followers": None,
                            "engagement": None
                        })
                elif platform == "twitter":
                    try:
                        from mcp_services import mcp__twitter__get_profile
                        # Placeholder - assuming MCP provides this
                        stats.append({
                            "platform": platform,
                            "status": "configured",
                            "followers": 0,  # Will be populated when MCP is called
                            "engagement": {}
                        })
                    except ImportError:
                        stats.append({
                            "platform": platform,
                            "status": "configured_no_mcp",
                            "message": "MCP server not available",
                            "followers": None,
                            "engagement": None
                        })
            except Exception as e:
                stats.append({
                    "platform": platform,
                    "status": "error",
                    "error": str(e),
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
    engagement_data = {
        "summary": {
            "total_followers": 0,
            "total_posts_this_week": 0,
            "total_engagement": 0,
            "top_platform": None
        },
        "platforms": {}
    }

    # Get Facebook insights
    try:
        if os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"):
            try:
                from mcp_services import mcp__facebook__get_page_insights
                facebook_insights = await mcp__facebook__get_page_insights()
                engagement_data["platforms"]["facebook"] = {
                    "configured": True,
                    "page_likes": facebook_insights.get("page_impressions", 0),
                    "reach": facebook_insights.get("page_engaged_users", 0),
                    "engagement_rate": None  # Calculated based on data
                }
                engagement_data["summary"]["total_followers"] += facebook_insights.get("page_fans", 0)
            except ImportError:
                engagement_data["platforms"]["facebook"] = {
                    "configured": True,
                    "page_likes": None,
                    "reach": None,
                    "engagement_rate": None,
                    "message": "MCP server not available"
                }
        else:
            engagement_data["platforms"]["facebook"] = {
                "configured": False,
                "page_likes": None,
                "reach": None,
                "engagement_rate": None
            }
    except Exception as e:
        engagement_data["platforms"]["facebook"] = {
            "configured": True,
            "page_likes": None,
            "reach": None,
            "engagement_rate": None,
            "error": str(e)
        }

    # Get Instagram insights
    try:
        if os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"):
            try:
                from mcp_services import mcp__instagram__get_insights
                instagram_insights = await mcp__instagram__get_insights()
                engagement_data["platforms"]["instagram"] = {
                    "configured": True,
                    "followers": instagram_insights.get("follower_count", 0),
                    "impressions": instagram_insights.get("impressions", 0),
                    "engagement_rate": None
                }
                engagement_data["summary"]["total_followers"] += instagram_insights.get("follower_count", 0)
            except ImportError:
                engagement_data["platforms"]["instagram"] = {
                    "configured": True,
                    "followers": None,
                    "impressions": None,
                    "engagement_rate": None,
                    "message": "MCP server not available"
                }
        else:
            engagement_data["platforms"]["instagram"] = {
                "configured": False,
                "followers": None,
                "impressions": None,
                "engagement_rate": None
            }
    except Exception as e:
        engagement_data["platforms"]["instagram"] = {
            "configured": True,
            "followers": None,
            "impressions": None,
            "engagement_rate": None,
            "error": str(e)
        }

    # Get LinkedIn profile
    try:
        if os.getenv("LINKEDIN_ACCESS_TOKEN"):
            try:
                from mcp_services import mcp__linkedin__get_profile
                linkedin_profile = await mcp__linkedin__get_profile()
                engagement_data["platforms"]["linkedin"] = {
                    "configured": True,
                    "connections": linkedin_profile.get("connections", 0),
                    "post_impressions": linkedin_profile.get("impressions", 0),
                    "engagement_rate": None
                }
                engagement_data["summary"]["total_followers"] += linkedin_profile.get("connections", 0)
            except ImportError:
                engagement_data["platforms"]["linkedin"] = {
                    "configured": True,
                    "connections": None,
                    "post_impressions": None,
                    "engagement_rate": None,
                    "message": "MCP server not available"
                }
        else:
            engagement_data["platforms"]["linkedin"] = {
                "configured": False,
                "connections": None,
                "post_impressions": None,
                "engagement_rate": None
            }
    except Exception as e:
        engagement_data["platforms"]["linkedin"] = {
            "configured": True,
            "connections": None,
            "post_impressions": None,
            "engagement_rate": None,
            "error": str(e)
        }

    # Get Twitter metrics
    try:
        if os.getenv("TWITTER_BEARER_TOKEN"):
            try:
                from mcp_services import mcp__twitter__get_metrics
                engagement_data["platforms"]["twitter"] = {
                    "configured": True,
                    "followers": 0,  # Will be populated when MCP is called
                    "tweet_impressions": 0,
                    "engagement_rate": None
                }
            except ImportError:
                engagement_data["platforms"]["twitter"] = {
                    "configured": True,
                    "followers": None,
                    "tweet_impressions": None,
                    "engagement_rate": None,
                    "message": "MCP server not available"
                }
        else:
            engagement_data["platforms"]["twitter"] = {
                "configured": False,
                "followers": None,
                "tweet_impressions": None,
                "engagement_rate": None
            }
    except Exception as e:
        engagement_data["platforms"]["twitter"] = {
            "configured": True,
            "followers": None,
            "tweet_impressions": None,
            "engagement_rate": None,
            "error": str(e)
        }

    # Determine top platform based on followers
    platform_followers = {}
    for platform, data in engagement_data["platforms"].items():
        if data.get("configured") and data.get("followers") is not None and data["followers"] is not None:
            platform_followers[platform] = data["followers"]

    if platform_followers:
        engagement_data["summary"]["top_platform"] = max(platform_followers, key=platform_followers.get)

    engagement_data["generated_at"] = datetime.now().isoformat()
    return engagement_data


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
