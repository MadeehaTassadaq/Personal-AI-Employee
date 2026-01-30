"""Twitter/X MCP tools definitions."""

TWITTER_TOOLS = [
    {
        "name": "post_tweet",
        "description": "Post a tweet to Twitter/X. Requires approval before execution. Max 280 characters.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Tweet content (max 280 characters)"
                },
                "reply_to": {
                    "type": "string",
                    "description": "Optional tweet ID to reply to"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "get_mentions",
        "description": "Get recent mentions of the authenticated user. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of mentions to retrieve (max 100)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_timeline",
        "description": "Get the home timeline of the authenticated user. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of tweets to retrieve (max 100)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_analytics",
        "description": "Get analytics for recent tweets from the authenticated user. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_user_info",
        "description": "Get information about the authenticated Twitter user. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_connection",
        "description": "Check if the Twitter API connection is working. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
