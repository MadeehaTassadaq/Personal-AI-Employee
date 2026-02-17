"""Instagram MCP tools definitions."""

INSTAGRAM_TOOLS = [
    {
        "name": "post_image",
        "description": "Post an image to Instagram. Requires approval before execution. Image must be at a public URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": "Public URL of the image to post (must be accessible by Instagram servers)"
                },
                "caption": {
                    "type": "string",
                    "description": "Caption for the post (max 2,200 characters, max 30 hashtags)"
                }
            },
            "required": ["image_url", "caption"]
        }
    },
    {
        "name": "post_carousel",
        "description": "Post a carousel (multiple images) to Instagram. Requires approval before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_urls": {
                    "type": "string",
                    "description": "Comma-separated list of public image URLs (2-10 images)"
                },
                "caption": {
                    "type": "string",
                    "description": "Caption for the carousel post"
                }
            },
            "required": ["image_urls", "caption"]
        }
    },
    {
        "name": "get_insights",
        "description": "Get Instagram account insights and analytics. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["impressions", "reach", "profile_views", "follower_count"],
                    "description": "Metric to retrieve",
                    "default": "impressions"
                }
            }
        }
    },
    {
        "name": "get_media",
        "description": "Get recent Instagram posts/media. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of posts to retrieve (max 50)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_account_info",
        "description": "Get Instagram business account information. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_connection",
        "description": "Check if the Instagram API connection is working. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
