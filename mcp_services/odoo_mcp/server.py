"""Odoo MCP Server for accounting and business operations.

Connects to Odoo Community Edition via JSON-RPC.
Supports invoicing, expenses, and financial reporting.
"""

import os
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from .jsonrpc_client import get_client, OdooClient

app = Server("odoo-mcp")

# Import healthcare tools to extend the MCP server
try:
    from . import healthcare_tools
    _healthcare_loaded = True
except ImportError:
    _healthcare_loaded = False

# Configuration
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def log_action(action: str, details: dict) -> None:
    """Log an MCP action."""
    log_dir = Path(os.getenv("VAULT_PATH", "./vault")) / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "OdooMCP",
        "event": action,
        **details
    }

    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            logs = []

    logs.append(entry)
    log_file.write_text(json.dumps(logs, indent=2))


@app.tool()
async def authenticate() -> str:
    """Authenticate with Odoo and verify connection.

    Returns:
        Authentication status and user info
    """
    log_action("odoo_auth_requested", {"dry_run": DRY_RUN})

    if DRY_RUN:
        return "[DRY RUN] Would authenticate with Odoo"

    try:
        client = get_client()
        uid = await client.authenticate()

        # Get user info
        users = await client.read("res.users", [uid], ["name", "login", "email"])
        user = users[0] if users else {}

        version = await client.version()

        log_action("odoo_authenticated", {"uid": uid, "user": user.get("login")})

        return (
            f"Odoo Authentication Successful:\n"
            f"- User ID: {uid}\n"
            f"- Name: {user.get('name', 'Unknown')}\n"
            f"- Login: {user.get('login', 'Unknown')}\n"
            f"- Server Version: {version.get('server_version', 'Unknown')}"
        )

    except Exception as e:
        log_action("odoo_auth_error", {"error": str(e)})
        return f"Authentication failed: {str(e)}"


@app.tool()
async def create_invoice(
    partner_name: str,
    product_name: str,
    quantity: float,
    unit_price: float,
    description: Optional[str] = None
) -> str:
    """Create a customer invoice.

    Args:
        partner_name: Customer/partner name (will be searched or created)
        product_name: Product or service name
        quantity: Quantity of items
        unit_price: Price per unit
        description: Optional line description

    Returns:
        Invoice ID and details or error message
    """
    log_action("odoo_invoice_requested", {
        "partner": partner_name,
        "product": product_name,
        "amount": quantity * unit_price,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        total = quantity * unit_price
        return (
            f"[DRY RUN] Would create invoice:\n"
            f"- Customer: {partner_name}\n"
            f"- Product: {product_name}\n"
            f"- Quantity: {quantity}\n"
            f"- Unit Price: ${unit_price:.2f}\n"
            f"- Total: ${total:.2f}"
        )

    try:
        client = get_client()
        await client.authenticate()

        # Find or create partner
        partners = await client.search_read(
            "res.partner",
            [("name", "ilike", partner_name)],
            ["id", "name"],
            limit=1
        )

        if partners:
            partner_id = partners[0]["id"]
        else:
            partner_id = await client.create("res.partner", {
                "name": partner_name,
                "is_company": True
            })

        # Find or create product
        products = await client.search_read(
            "product.product",
            [("name", "ilike", product_name)],
            ["id", "name", "list_price"],
            limit=1
        )

        if products:
            product_id = products[0]["id"]
        else:
            # Create a service product
            product_tmpl_id = await client.create("product.template", {
                "name": product_name,
                "type": "service",
                "list_price": unit_price
            })
            products = await client.search_read(
                "product.product",
                [("product_tmpl_id", "=", product_tmpl_id)],
                ["id"],
                limit=1
            )
            product_id = products[0]["id"]

        # Create invoice
        invoice_vals = {
            "partner_id": partner_id,
            "move_type": "out_invoice",  # Customer invoice
            "invoice_date": date.today().isoformat(),
            "invoice_line_ids": [(0, 0, {
                "product_id": product_id,
                "name": description or product_name,
                "quantity": quantity,
                "price_unit": unit_price
            })]
        }

        invoice_id = await client.create("account.move", invoice_vals)

        # Read the created invoice
        invoices = await client.read(
            "account.move",
            [invoice_id],
            ["name", "amount_total", "state"]
        )
        invoice = invoices[0]

        log_action("odoo_invoice_created", {
            "invoice_id": invoice_id,
            "name": invoice.get("name"),
            "amount": invoice.get("amount_total")
        })

        return (
            f"Invoice created successfully:\n"
            f"- Invoice Number: {invoice.get('name', 'Draft')}\n"
            f"- Invoice ID: {invoice_id}\n"
            f"- Customer: {partner_name}\n"
            f"- Total: ${invoice.get('amount_total', 0):.2f}\n"
            f"- Status: {invoice.get('state', 'draft')}"
        )

    except Exception as e:
        log_action("odoo_invoice_error", {"error": str(e)})
        return f"Error creating invoice: {str(e)}"


@app.tool()
async def get_account_balance() -> str:
    """Get current account balances.

    Returns:
        Summary of account balances
    """
    log_action("odoo_balance_requested", {"dry_run": DRY_RUN})

    if DRY_RUN:
        return "[DRY RUN] Would fetch Odoo account balances"

    try:
        client = get_client()
        await client.authenticate()

        # Get bank/cash accounts
        accounts = await client.search_read(
            "account.account",
            [("account_type", "in", ["asset_cash", "asset_bank"])],
            ["name", "code", "current_balance"],
            limit=20
        )

        if not accounts:
            return "No bank/cash accounts found"

        result = "Account Balances:\n\n"
        total = 0.0

        for acc in accounts:
            balance = acc.get("current_balance", 0)
            total += balance
            result += f"{acc.get('code')} - {acc.get('name')}: ${balance:.2f}\n"

        result += f"\nTotal Cash/Bank: ${total:.2f}"

        return result

    except Exception as e:
        log_action("odoo_balance_error", {"error": str(e)})
        return f"Error getting balances: {str(e)}"


@app.tool()
async def list_invoices(
    state: str = "all",
    invoice_type: str = "customer",
    limit: int = 20
) -> str:
    """List invoices from Odoo.

    Args:
        state: Filter by state - "all", "draft", "posted", "paid", "cancel"
        invoice_type: Type of invoices - "customer" or "vendor"
        limit: Maximum number of invoices to return

    Returns:
        List of invoices or error message
    """
    log_action("odoo_invoices_requested", {
        "state": state,
        "type": invoice_type,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return f"[DRY RUN] Would list {invoice_type} invoices with state: {state}"

    try:
        client = get_client()
        await client.authenticate()

        # Build domain
        domain = []

        if invoice_type == "customer":
            domain.append(("move_type", "=", "out_invoice"))
        else:
            domain.append(("move_type", "=", "in_invoice"))

        if state != "all":
            if state == "paid":
                domain.append(("payment_state", "=", "paid"))
            else:
                domain.append(("state", "=", state))

        invoices = await client.search_read(
            "account.move",
            domain,
            ["name", "partner_id", "invoice_date", "amount_total", "state", "payment_state"],
            limit=limit,
            order="invoice_date desc"
        )

        if not invoices:
            return f"No {invoice_type} invoices found"

        type_label = "Customer" if invoice_type == "customer" else "Vendor"
        result = f"{type_label} Invoices:\n\n"

        total_amount = 0
        for inv in invoices:
            partner = inv.get("partner_id", [0, "Unknown"])
            partner_name = partner[1] if isinstance(partner, list) else "Unknown"
            amount = inv.get("amount_total", 0)
            total_amount += amount

            result += f"{inv.get('name', 'Draft')} | {partner_name}\n"
            result += f"  Date: {inv.get('invoice_date', 'N/A')}\n"
            result += f"  Amount: ${amount:.2f}\n"
            result += f"  Status: {inv.get('state', 'draft')} / Payment: {inv.get('payment_state', 'not_paid')}\n\n"

        result += f"Total: ${total_amount:.2f} ({len(invoices)} invoices)"

        return result

    except Exception as e:
        log_action("odoo_invoices_error", {"error": str(e)})
        return f"Error listing invoices: {str(e)}"


@app.tool()
async def create_expense(
    name: str,
    amount: float,
    category: str = "general",
    date_str: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """Record a business expense in Odoo.

    Args:
        name: Expense description
        amount: Expense amount
        category: Category - "travel", "office", "meals", "general"
        date_str: Expense date (YYYY-MM-DD format, defaults to today)
        notes: Additional notes

    Returns:
        Expense record details or error message
    """
    log_action("odoo_expense_requested", {
        "name": name,
        "amount": amount,
        "category": category,
        "dry_run": DRY_RUN
    })

    if DRY_RUN:
        return (
            f"[DRY RUN] Would create expense:\n"
            f"- Description: {name}\n"
            f"- Amount: ${amount:.2f}\n"
            f"- Category: {category}\n"
            f"- Date: {date_str or 'today'}"
        )

    try:
        client = get_client()
        await client.authenticate()

        # Get current user's employee record
        users = await client.search_read(
            "res.users",
            [("id", "=", client.uid)],
            ["employee_id"],
            limit=1
        )

        employee_id = None
        if users and users[0].get("employee_id"):
            employee_id = users[0]["employee_id"][0]

        # Find or create expense product
        category_map = {
            "travel": "Travel Expenses",
            "office": "Office Supplies",
            "meals": "Meals & Entertainment",
            "general": "General Expenses"
        }
        product_name = category_map.get(category, "General Expenses")

        products = await client.search_read(
            "product.product",
            [("name", "=", product_name), ("can_be_expensed", "=", True)],
            ["id"],
            limit=1
        )

        if products:
            product_id = products[0]["id"]
        else:
            # Create expense product
            product_tmpl_id = await client.create("product.template", {
                "name": product_name,
                "type": "service",
                "can_be_expensed": True,
                "list_price": 0
            })
            products = await client.search_read(
                "product.product",
                [("product_tmpl_id", "=", product_tmpl_id)],
                ["id"],
                limit=1
            )
            product_id = products[0]["id"]

        expense_date = date_str or date.today().isoformat()

        expense_vals = {
            "name": name,
            "product_id": product_id,
            "total_amount": amount,
            "date": expense_date,
            "description": notes or ""
        }

        if employee_id:
            expense_vals["employee_id"] = employee_id

        expense_id = await client.create("hr.expense", expense_vals)

        log_action("odoo_expense_created", {
            "expense_id": expense_id,
            "amount": amount,
            "category": category
        })

        return (
            f"Expense created successfully:\n"
            f"- ID: {expense_id}\n"
            f"- Description: {name}\n"
            f"- Amount: ${amount:.2f}\n"
            f"- Category: {category}\n"
            f"- Date: {expense_date}"
        )

    except Exception as e:
        log_action("odoo_expense_error", {"error": str(e)})
        return f"Error creating expense: {str(e)}"


@app.tool()
async def get_financial_summary() -> str:
    """Get a financial summary for CEO briefing.

    Returns:
        Financial overview including revenue, expenses, and cash position
    """
    log_action("odoo_summary_requested", {"dry_run": DRY_RUN})

    if DRY_RUN:
        return "[DRY RUN] Would generate Odoo financial summary"

    try:
        client = get_client()
        await client.authenticate()

        result = "Financial Summary:\n\n"

        # Get receivables (unpaid customer invoices)
        receivables = await client.search_read(
            "account.move",
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "!=", "paid")
            ],
            ["amount_total", "amount_residual"],
            limit=100
        )

        total_receivable = sum(inv.get("amount_residual", 0) for inv in receivables)
        result += f"Accounts Receivable:\n"
        result += f"  Outstanding: ${total_receivable:.2f} ({len(receivables)} invoices)\n\n"

        # Get payables (unpaid vendor bills)
        payables = await client.search_read(
            "account.move",
            [
                ("move_type", "=", "in_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "!=", "paid")
            ],
            ["amount_total", "amount_residual"],
            limit=100
        )

        total_payable = sum(inv.get("amount_residual", 0) for inv in payables)
        result += f"Accounts Payable:\n"
        result += f"  Outstanding: ${total_payable:.2f} ({len(payables)} bills)\n\n"

        # Get this month's revenue
        this_month_start = date.today().replace(day=1).isoformat()
        month_invoices = await client.search_read(
            "account.move",
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("invoice_date", ">=", this_month_start)
            ],
            ["amount_total"],
            limit=500
        )

        month_revenue = sum(inv.get("amount_total", 0) for inv in month_invoices)
        result += f"This Month:\n"
        result += f"  Revenue: ${month_revenue:.2f} ({len(month_invoices)} invoices)\n\n"

        # Get cash position
        try:
            accounts = await client.search_read(
                "account.account",
                [("account_type", "in", ["asset_cash", "asset_bank"])],
                ["name", "current_balance"],
                limit=10
            )
            cash_total = sum(acc.get("current_balance", 0) for acc in accounts)
            result += f"Cash Position: ${cash_total:.2f}\n\n"
        except Exception:
            result += "Cash Position: Unable to retrieve\n\n"

        # Summary
        result += "Key Metrics:\n"
        result += f"  Net Position: ${cash_total + total_receivable - total_payable:.2f}\n"
        result += f"  AR/AP Ratio: {total_receivable / max(total_payable, 1):.2f}\n"

        return result

    except Exception as e:
        log_action("odoo_summary_error", {"error": str(e)})
        return f"Error generating summary: {str(e)}"


@app.tool()
async def check_connection() -> str:
    """Check if Odoo connection is working.

    Returns:
        Connection status
    """
    try:
        client = get_client()
        version = await client.version()

        server_version = version.get("server_version", "Unknown")
        return f"Odoo connection is active. Server version: {server_version}"

    except Exception as e:
        return f"Connection check failed: {str(e)}"


if __name__ == "__main__":
    app.run()
