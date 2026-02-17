"""Odoo MCP tools definitions."""

ODOO_TOOLS = [
    {
        "name": "authenticate",
        "description": "Authenticate with Odoo and verify connection. Auto-approved.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_invoice",
        "description": "Create a customer invoice in Odoo. Requires approval before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "partner_name": {
                    "type": "string",
                    "description": "Customer/partner name (will be searched or created)"
                },
                "product_name": {
                    "type": "string",
                    "description": "Product or service name"
                },
                "quantity": {
                    "type": "number",
                    "description": "Quantity of items"
                },
                "unit_price": {
                    "type": "number",
                    "description": "Price per unit"
                },
                "description": {
                    "type": "string",
                    "description": "Optional line description"
                }
            },
            "required": ["partner_name", "product_name", "quantity", "unit_price"]
        }
    },
    {
        "name": "get_account_balance",
        "description": "Get current account balances from Odoo. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_invoices",
        "description": "List invoices from Odoo. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["all", "draft", "posted", "paid", "cancel"],
                    "description": "Filter by invoice state",
                    "default": "all"
                },
                "invoice_type": {
                    "type": "string",
                    "enum": ["customer", "vendor"],
                    "description": "Type of invoices to list",
                    "default": "customer"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of invoices to return",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "create_expense",
        "description": "Record a business expense in Odoo. Requires approval before execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Expense description"
                },
                "amount": {
                    "type": "number",
                    "description": "Expense amount"
                },
                "category": {
                    "type": "string",
                    "enum": ["travel", "office", "meals", "general"],
                    "description": "Expense category",
                    "default": "general"
                },
                "date_str": {
                    "type": "string",
                    "description": "Expense date in YYYY-MM-DD format (defaults to today)"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes"
                }
            },
            "required": ["name", "amount"]
        }
    },
    {
        "name": "get_financial_summary",
        "description": "Get a financial summary for CEO briefing. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_connection",
        "description": "Check if the Odoo connection is working. Auto-approved (read-only).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
