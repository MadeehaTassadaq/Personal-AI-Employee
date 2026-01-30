---
name: odoo-accounting
description: Manage accounting operations via Odoo Community Edition MCP server. Use when Claude needs to (1) create customer invoices, (2) record business expenses, (3) check account balances, (4) list invoices, or (5) generate financial summaries. Invoice and expense creation require approval. Read operations are auto-approved.
---

# Odoo Accounting

Manage accounting and financial operations via Odoo Community Edition.

## Setup Requirements

Odoo must be running and accessible. Recommended setup via Docker:

```bash
# Start Odoo (see docs/ARCHITECTURE.md for full setup)
docker compose -f odoo-docker/docker-compose.yml up -d
# Access at http://localhost:8069
```

Required environment variables:
```
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

## MCP Tools

### Read Operations (Auto-Approved)

```
Tool: odoo_authenticate
Description: Verify Odoo connection and get user info

Tool: odoo_get_account_balance
Description: Get current bank/cash account balances

Tool: odoo_list_invoices
Parameters:
  - state: "all" | "draft" | "posted" | "paid" | "cancel"
  - invoice_type: "customer" | "vendor"
  - limit: number (default 20)

Tool: odoo_get_financial_summary
Description: Get financial overview for CEO briefing

Tool: odoo_check_connection
Description: Verify Odoo server is accessible
```

### Write Operations (Require Approval)

```
Tool: odoo_create_invoice
Parameters:
  - partner_name: string (customer name)
  - product_name: string (service/product)
  - quantity: number
  - unit_price: number
  - description: string (optional)

Tool: odoo_create_expense
Parameters:
  - name: string (expense description)
  - amount: number
  - category: "travel" | "office" | "meals" | "general"
  - date_str: string (YYYY-MM-DD, optional)
  - notes: string (optional)
```

## Approval Workflow

**Invoice and expense creation require human approval.**

1. **Create approval request**: Write file to `$VAULT_PATH/Pending_Approval/`
2. **Wait for approval**: File moved to `$VAULT_PATH/Approved/`
3. **Check DRY_RUN**: If true, log but don't create
4. **Execute via MCP**: Call appropriate Odoo tool
5. **Log action**: Record in `$VAULT_PATH/Logs/`
6. **Move to Done**: Move approval file to Done folder

## Invoice Approval File Format

```markdown
---
type: odoo_invoice
status: pending_approval
created: {{ISO_DATE}}
---

# Invoice Approval Request

**Customer:** {{partner_name}}
**Product/Service:** {{product_name}}
**Quantity:** {{quantity}}
**Unit Price:** ${{unit_price}}
**Total:** ${{quantity * unit_price}}

## Description
{{Line item description}}

## Context
{{Why this invoice is being created}}

## Approval
- [ ] Approved by CEO
```

## Expense Approval File Format

```markdown
---
type: odoo_expense
status: pending_approval
created: {{ISO_DATE}}
---

# Expense Approval Request

**Description:** {{name}}
**Amount:** ${{amount}}
**Category:** {{category}}
**Date:** {{date_str or today}}

## Notes
{{Additional notes}}

## Receipt
{{Link to receipt if available}}

## Approval
- [ ] Approved by CEO
```

## Financial Summary Format

The `get_financial_summary` tool returns:

```
Financial Summary:

Accounts Receivable:
  Outstanding: $X,XXX.XX (N invoices)

Accounts Payable:
  Outstanding: $X,XXX.XX (N bills)

This Month:
  Revenue: $X,XXX.XX (N invoices)

Cash Position: $X,XXX.XX

Key Metrics:
  Net Position: $X,XXX.XX
  AR/AP Ratio: X.XX
```

## CEO Briefing Integration

This skill integrates with the `weekly-briefing` and `ceo-briefing-gold` skills:

1. Call `odoo_get_financial_summary` for financial metrics
2. Call `odoo_list_invoices` for outstanding invoices
3. Include data in CEO briefing report

## Best Practices

- Verify Odoo connection before operations
- Use descriptive names for partners and products
- Include context in approval requests
- Review financial summary weekly
- Reconcile accounts monthly

## Rules

- NEVER create invoices/expenses without approval
- Check DRY_RUN before making changes
- Log all operations in vault/Logs/
- Verify amounts before approval submission
- Keep partner names consistent
