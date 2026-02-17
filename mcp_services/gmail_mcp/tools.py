"""Gmail MCP tools definitions."""

GMAIL_TOOLS = [
    {
        "name": "send_email",
        "description": "Send an email via Gmail. Requires approval before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "cc": {
                    "type": "string",
                    "description": "CC recipients (comma-separated)",
                    "default": ""
                },
                "bcc": {
                    "type": "string",
                    "description": "BCC recipients (comma-separated)",
                    "default": ""
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "draft_email",
        "description": "Create a draft email without sending. Safe operation, doesn't require approval.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "search_emails",
        "description": "Search emails in Gmail inbox using Gmail search syntax.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'from:user@example.com subject:hello')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
]
