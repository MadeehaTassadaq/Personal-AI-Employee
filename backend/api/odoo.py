"""Odoo integration API endpoints."""

import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


def is_odoo_configured() -> bool:
    """Check if Odoo environment variables are set."""
    return all([
        os.getenv("ODOO_URL"),
        os.getenv("ODOO_DB"),
        os.getenv("ODOO_USERNAME"),
        os.getenv("ODOO_PASSWORD")
    ])


class InvoiceRequest(BaseModel):
    """Request model for creating an invoice."""
    partner_name: str
    product_name: str
    quantity: float
    unit_price: float
    description: Optional[str] = None


class ExpenseRequest(BaseModel):
    """Request model for creating an expense."""
    name: str
    amount: float
    category: str = "general"
    date_str: Optional[str] = None
    notes: Optional[str] = None


def get_odoo_client():
    """Get Odoo client from MCP server."""
    mcp_path = Path(os.getcwd()) / "mcp/odoo-mcp"
    if str(mcp_path) not in sys.path:
        sys.path.insert(0, str(mcp_path))

    from jsonrpc_client import get_client
    return get_client()


@router.get("/health")
async def check_odoo_health():
    """Check Odoo integration health status.

    Returns:
        Health status - configured, connected, or not_configured
    """
    if not is_odoo_configured():
        return {
            "status": "not_configured",
            "message": "Odoo integration disabled. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD in .env to enable.",
            "checked_at": datetime.now().isoformat()
        }

    try:
        client = get_odoo_client()
        version = await client.version()

        return {
            "status": "healthy",
            "server_version": version.get("server_version", "unknown"),
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Odoo is configured but connection failed",
            "checked_at": datetime.now().isoformat()
        }


@router.get("/status")
async def check_odoo_status():
    """Check Odoo connection status.

    Returns:
        Connection status and server version
    """
    if not is_odoo_configured():
        return {
            "status": "not_configured",
            "message": "Odoo integration disabled",
            "checked_at": datetime.now().isoformat()
        }

    try:
        client = get_odoo_client()
        version = await client.version()

        return {
            "status": "connected",
            "server_version": version.get("server_version", "unknown"),
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }


@router.get("/balance")
async def get_account_balance():
    """Get current account balances from Odoo.

    Returns:
        List of account balances
    """
    try:
        client = get_odoo_client()
        await client.authenticate()

        accounts = await client.search_read(
            "account.account",
            [("account_type", "in", ["asset_cash", "asset_bank"])],
            ["name", "code", "current_balance"],
            limit=20
        )

        total = sum(acc.get("current_balance", 0) for acc in accounts)

        return {
            "accounts": [
                {
                    "code": acc.get("code"),
                    "name": acc.get("name"),
                    "balance": acc.get("current_balance", 0)
                }
                for acc in accounts
            ],
            "total": total,
            "retrieved_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balances: {str(e)}")


@router.get("/invoices")
async def list_invoices(
    state: str = Query("all", description="Invoice state filter"),
    invoice_type: str = Query("customer", description="customer or vendor"),
    limit: int = Query(20, ge=1, le=100)
):
    """List invoices from Odoo.

    Args:
        state: Filter by state (all, draft, posted, paid, cancel)
        invoice_type: Type of invoices (customer or vendor)
        limit: Maximum number to return

    Returns:
        List of invoices
    """
    try:
        client = get_odoo_client()
        await client.authenticate()

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
            ["name", "partner_id", "invoice_date", "amount_total", "amount_residual", "state", "payment_state"],
            limit=limit,
            order="invoice_date desc"
        )

        return {
            "invoices": [
                {
                    "id": inv.get("id"),
                    "name": inv.get("name"),
                    "partner": inv.get("partner_id", [0, "Unknown"])[1] if isinstance(inv.get("partner_id"), list) else "Unknown",
                    "date": inv.get("invoice_date"),
                    "total": inv.get("amount_total", 0),
                    "residual": inv.get("amount_residual", 0),
                    "state": inv.get("state"),
                    "payment_state": inv.get("payment_state")
                }
                for inv in invoices
            ],
            "count": len(invoices),
            "retrieved_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list invoices: {str(e)}")


@router.get("/summary")
async def get_financial_summary():
    """Get financial summary for dashboards and briefings.

    Returns:
        Financial overview including AR, AP, and cash position
    """
    try:
        client = get_odoo_client()
        await client.authenticate()

        # Accounts Receivable
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
        ar_total = sum(inv.get("amount_residual", 0) for inv in receivables)
        ar_count = len(receivables)

        # Accounts Payable
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
        ap_total = sum(inv.get("amount_residual", 0) for inv in payables)
        ap_count = len(payables)

        # This month revenue
        from datetime import date
        month_start = date.today().replace(day=1).isoformat()
        month_invoices = await client.search_read(
            "account.move",
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("invoice_date", ">=", month_start)
            ],
            ["amount_total"],
            limit=500
        )
        month_revenue = sum(inv.get("amount_total", 0) for inv in month_invoices)

        # Cash position
        try:
            accounts = await client.search_read(
                "account.account",
                [("account_type", "in", ["asset_cash", "asset_bank"])],
                ["current_balance"],
                limit=10
            )
            cash_total = sum(acc.get("current_balance", 0) for acc in accounts)
        except Exception:
            cash_total = None

        return {
            "accounts_receivable": {
                "total": ar_total,
                "count": ar_count
            },
            "accounts_payable": {
                "total": ap_total,
                "count": ap_count
            },
            "month_revenue": month_revenue,
            "cash_position": cash_total,
            "net_position": (cash_total or 0) + ar_total - ap_total,
            "ar_ap_ratio": ar_total / max(ap_total, 1),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.post("/invoice")
async def create_invoice(request: InvoiceRequest):
    """Create a customer invoice in Odoo.

    Note: In production, this should go through the approval workflow.

    Args:
        request: Invoice details

    Returns:
        Created invoice information
    """
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        return {
            "status": "dry_run",
            "message": "Would create invoice",
            "details": request.model_dump()
        }

    try:
        client = get_odoo_client()
        await client.authenticate()

        # Find or create partner
        partners = await client.search_read(
            "res.partner",
            [("name", "ilike", request.partner_name)],
            ["id", "name"],
            limit=1
        )

        if partners:
            partner_id = partners[0]["id"]
        else:
            partner_id = await client.create("res.partner", {
                "name": request.partner_name,
                "is_company": True
            })

        # Find or create product
        products = await client.search_read(
            "product.product",
            [("name", "ilike", request.product_name)],
            ["id"],
            limit=1
        )

        if products:
            product_id = products[0]["id"]
        else:
            product_tmpl_id = await client.create("product.template", {
                "name": request.product_name,
                "type": "service",
                "list_price": request.unit_price
            })
            products = await client.search_read(
                "product.product",
                [("product_tmpl_id", "=", product_tmpl_id)],
                ["id"],
                limit=1
            )
            product_id = products[0]["id"]

        # Create invoice
        from datetime import date
        invoice_id = await client.create("account.move", {
            "partner_id": partner_id,
            "move_type": "out_invoice",
            "invoice_date": date.today().isoformat(),
            "invoice_line_ids": [(0, 0, {
                "product_id": product_id,
                "name": request.description or request.product_name,
                "quantity": request.quantity,
                "price_unit": request.unit_price
            })]
        })

        invoices = await client.read(
            "account.move",
            [invoice_id],
            ["name", "amount_total", "state"]
        )
        invoice = invoices[0]

        return {
            "status": "created",
            "invoice_id": invoice_id,
            "name": invoice.get("name"),
            "total": invoice.get("amount_total"),
            "state": invoice.get("state"),
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")


@router.post("/expense")
async def create_expense(request: ExpenseRequest):
    """Create a business expense in Odoo.

    Note: In production, this should go through the approval workflow.

    Args:
        request: Expense details

    Returns:
        Created expense information
    """
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if dry_run:
        return {
            "status": "dry_run",
            "message": "Would create expense",
            "details": request.model_dump()
        }

    try:
        client = get_odoo_client()
        await client.authenticate()

        category_map = {
            "travel": "Travel Expenses",
            "office": "Office Supplies",
            "meals": "Meals & Entertainment",
            "general": "General Expenses"
        }
        product_name = category_map.get(request.category, "General Expenses")

        products = await client.search_read(
            "product.product",
            [("name", "=", product_name), ("can_be_expensed", "=", True)],
            ["id"],
            limit=1
        )

        if products:
            product_id = products[0]["id"]
        else:
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

        from datetime import date
        expense_date = request.date_str or date.today().isoformat()

        expense_id = await client.create("hr.expense", {
            "name": request.name,
            "product_id": product_id,
            "total_amount": request.amount,
            "date": expense_date,
            "description": request.notes or ""
        })

        return {
            "status": "created",
            "expense_id": expense_id,
            "name": request.name,
            "amount": request.amount,
            "category": request.category,
            "date": expense_date,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create expense: {str(e)}")
