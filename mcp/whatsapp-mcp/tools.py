"""WhatsApp MCP tools definitions."""

WHATSAPP_TOOLS = [
    {
        "name": "send_message",
        "description": "Send a WhatsApp message. Requires approval before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Phone number with country code (e.g., +1234567890)"
                },
                "message": {
                    "type": "string",
                    "description": "Message content to send"
                }
            },
            "required": ["phone", "message"]
        }
    },
    {
        "name": "check_session",
        "description": "Check if WhatsApp Web session is active and logged in.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_unread_count",
        "description": "Get the count of chats with unread messages.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
