"""Browser MCP tools definitions."""

BROWSER_TOOLS = [
    {
        "name": "navigate",
        "description": "Navigate to a URL in the browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to navigate to"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "get_page_content",
        "description": "Get the text content of the current page.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot of the current page.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name for the screenshot file",
                    "default": "screenshot.png"
                }
            }
        }
    },
    {
        "name": "click",
        "description": "Click an element on the page using CSS selector.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the element to click"
                }
            },
            "required": ["selector"]
        }
    },
    {
        "name": "fill_input",
        "description": "Fill an input field with text.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the input field"
                },
                "text": {
                    "type": "string",
                    "description": "Text to fill in the input"
                }
            },
            "required": ["selector", "text"]
        }
    },
    {
        "name": "close_browser",
        "description": "Close the browser instance.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
