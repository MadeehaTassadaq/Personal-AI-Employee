"""Facebook MCP tools definitions."""

FACEBOOK_TOOLS = [
    {
        "name": "post_to_page",
        "description": "Create a post on the Facebook Page. Requires approval before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Post content (text, max 63,206 characters)"
                },
                "link": {
                    "type": "string",
                    "description": "Optional URL to include with the post"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "get_page_insights",
        "description": "Get Facebook Page insights and analytics. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "page_impressions",
                        "page_engaged_users",
                        "page_post_engagements",
                        "page_fans"
                    ],
                    "description": "Metric to retrieve",
                    "default": "page_impressions"
                },
                "period": {
                    "type": "string",
                    "enum": ["day", "week", "days_28"],
                    "description": "Time period for the metric",
                    "default": "day"
                }
            }
        }
    },
    {
        "name": "get_page_notifications",
        "description": "Get recent notifications and activity for the Facebook Page. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_page_info",
        "description": "Get basic information about the Facebook Page. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_connection",
        "description": "Check if the Facebook API connection is working. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
