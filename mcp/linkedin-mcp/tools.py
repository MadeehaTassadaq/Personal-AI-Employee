"""LinkedIn MCP tools definitions."""

LINKEDIN_TOOLS = [
    {
        "name": "create_post",
        "description": "Create a LinkedIn post. Requires approval before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Post content (text, max 3000 characters)"
                },
                "visibility": {
                    "type": "string",
                    "enum": ["PUBLIC", "CONNECTIONS"],
                    "description": "Post visibility",
                    "default": "PUBLIC"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "get_profile",
        "description": "Get the current user's LinkedIn profile information.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_connection",
        "description": "Check if the LinkedIn API connection is working.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
