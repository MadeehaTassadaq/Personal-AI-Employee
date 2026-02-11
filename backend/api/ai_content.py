"""AI Content Generation API endpoints."""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ai_reasoning import get_ai_reasoning_service, TaskContext

router = APIRouter()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault"))


class GenerateContentRequest(BaseModel):
    platform: str
    context: str
    options: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "linkedin",
                "context": "Share insights about AI in healthcare",
                "options": {
                    "recipient": None,
                    "subject": None
                }
            }
        }


class GenerateContentResponse(BaseModel):
    content: str
    subject: Optional[str] = None
    hashtags: Optional[list[str]] = None
    confidence: float
    fallback_used: bool = False


@router.post("/generate-content", response_model=GenerateContentResponse)
async def generate_ai_content(request: GenerateContentRequest):
    """Generate AI content for the specified platform.

    Uses the AI Reasoning Service to generate platform-specific content
    optimized for engagement and format requirements.

    Args:
        request: Content generation request with platform, context, and options

    Returns:
        Generated content with optional subject, hashtags, and confidence score

    Raises:
        HTTPException: If platform is not supported
    """
    # Validate platform
    supported_platforms = ["linkedin", "facebook", "instagram", "twitter", "email", "whatsapp"]
    if request.platform not in supported_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platform: {request.platform}. "
                   f"Supported platforms: {', '.join(supported_platforms)}"
        )

    # Get AI reasoning service
    ai_service = get_ai_reasoning_service(str(VAULT_PATH))

    # Build task context
    options = request.options or {}
    context = TaskContext(
        task_id=f"ai_generate_{request.platform}",
        task_type="social" if request.platform in ["linkedin", "facebook", "instagram", "twitter"] else request.platform,
        title=request.context[:100],
        platform=request.platform,
        description=request.context,
        recipient=options.get("recipient"),
        subject=options.get("subject"),
    )

    # Generate content based on platform type
    try:
        if request.platform == "email":
            generated = await ai_service.generate_email_content(context)
            return GenerateContentResponse(
                content=generated.content,
                subject=generated.subject,
                hashtags=[],
                confidence=generated.confidence,
                fallback_used=generated.fallback_used,
            )

        elif request.platform == "whatsapp":
            generated = await ai_service.generate_whatsapp_message(context)
            return GenerateContentResponse(
                content=generated.content,
                subject=None,
                hashtags=[],
                confidence=generated.confidence,
                fallback_used=generated.fallback_used,
            )

        else:  # Social media platforms
            generated = await ai_service.generate_social_post(context, request.platform)
            return GenerateContentResponse(
                content=generated.content,
                subject=None,
                hashtags=generated.hashtags,
                confidence=generated.confidence,
                fallback_used=generated.fallback_used,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate content: {str(e)}"
        )


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms for AI content generation."""
    return {
        "platforms": [
            {
                "id": "linkedin",
                "name": "LinkedIn",
                "maxLength": 3000,
                "supportsHashtags": True,
                "maxHashtags": 5,
                "description": "Professional posts and thought leadership"
            },
            {
                "id": "facebook",
                "name": "Facebook",
                "maxLength": 63206,
                "supportsHashtags": True,
                "maxHashtags": 2,
                "description": "Conversational, community-focused posts"
            },
            {
                "id": "instagram",
                "name": "Instagram",
                "maxLength": 2200,
                "supportsHashtags": True,
                "maxHashtags": 30,
                "description": "Visual-focused posts with hashtags"
            },
            {
                "id": "twitter",
                "name": "Twitter/X",
                "maxLength": 280,
                "supportsHashtags": True,
                "maxHashtags": 2,
                "description": "Concise updates and engagement"
            },
            {
                "id": "email",
                "name": "Email",
                "supportsHashtags": False,
                "description": "Professional email correspondence"
            },
            {
                "id": "whatsapp",
                "name": "WhatsApp",
                "maxLength": 500,
                "supportsHashtags": False,
                "description": "Brief, friendly messages"
            }
        ]
    }


@router.get("/health")
async def health_check():
    """Check if AI content generation service is available."""
    try:
        ai_service = get_ai_reasoning_service(str(VAULT_PATH))
        # Check if Claude API is configured
        api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        return {
            "status": "available",
            "claude_configured": bool(api_key),
            "fallback_available": True
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "fallback_available": True
        }
