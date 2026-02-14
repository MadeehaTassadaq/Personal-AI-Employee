# Healthcare Billing Skill

## Description
Generate patient invoices for healthcare services and process payments through Odoo accounting.

## Triggers
- Patient visit completed (billing needed)
- Invoice request from task
- Pending_Approval/ folder contains invoice task

## MCP Tools Used
- `odoo_mcp.get_patient` - Get patient info
- `odoo_mcp.create_patient_invoice` - Generate invoice
- `odoo_mcp.get_patient_invoices` - Check existing invoices
- `vault_reader` - Access approval tasks
- `task_mover` - Move tasks between folders

## Task Format (Requires Approval)
```yaml
---
title: "Generate Invoice - {Patient Name}"
created: 2026-02-13
priority: normal
status: pending_approval
type: healthcare_billing
assignee: human
tags: [healthcare, billing, invoice]

## Description
Generate invoice for **{Patient Name}** for services rendered on {service_date}.

## Patient Details
- **Patient:** {patient_name}
- **Patient ID:** {patient_id}
- **MRN:** {medical_record_number}

## Services Billed
{service_items}

## Invoice Details
- **Date:** {invoice_date}
- **Total Amount:** ${total_amount}
- **Insurance:** {insurance_provider} ({policy_number})

## Approval Required
This invoice requires human approval before sending to patient.

## Items
1. [ ] Review invoice details
2. [ ] Verify services were provided
3. [ ] Check insurance coverage if applicable
4. [ ] Approve invoice generation
5. [ ] Move to Approved/ for execution
```

## Execution Flow

### 1. Parse Task (After Approval)
Extract from approved task:
- `patient_id` - Patient record ID
- `service_items` - List of services with amounts
- `invoice_date` - Invoice date (defaults to today)

### 2. Verify Patient
```python
# Use MCP tool
patient = await mcp.odoo_mcp.get_patient(patient_id)

# Check insurance info
if patient.get('insurance_provider'):
    # Apply insurance rules
    # Adjust amounts based on coverage
```

### 3. Check Existing Invoices
```python
# Use MCP tool
existing = await mcp.odoo_mcp.get_patient_invoices(patient_id)

# Check for duplicate billing
# Verify this service hasn't been billed already
```

### 4. Create Invoice
```python
# Use MCP tool
items = [
    {"description": "Consultation", "amount": 50.00, "quantity": 1},
    {"description": "Vitals Check", "amount": 25.00, "quantity": 1},
    # Add procedure, lab, medication items
]

invoice = await mcp.odoo_mcp.create_patient_invoice(
    patient_id=patient_id,
    items=items,
    date=invoice_date
)
```

### 5. Record Invoice in Vault
```python
# Create invoice record
vault.create_task(
    title=f"Invoice Generated - {patient_name}",
    description=f"""
Invoice {invoice['name']} created for {patient_name}

Amount: ${invoice['amount_total']}
Status: {invoice['state']}
Items: {len(items)} services
    """,
    folder="Done/",
    tags=["healthcare", "billing", "invoice"]
)
```

### 6. Update Dashboard
```python
vault.update_dashboard(
    section="Healthcare",
    update=f"""
### Billing Update
- Invoice {invoice['name']} generated for {patient_name}
- Amount: ${invoice['amount_total']}
- Status: {invoice['state']}
    """
)
```

## Service Items Reference

### Common Services
| Code | Description | Amount |
|------|-------------|--------|
| CONSULT | General Consultation | $50 |
| FOLLOWUP | Follow-up Visit | $35 |
| CHECKUP | Regular Check-up | $60 |
| EMERGENCY | Emergency Visit | $150 |
| PRENATAL | Prenatal Checkup | $75 |
| LAB_TEST | Lab Test Processing | $40 |
| VACCINE | Vaccination | $30 |
| VITALS | Vitals Check | $25 |

### Procedure Pricing
| Procedure | Base Price | Notes |
|-----------|------------|-------|
| Wound Care | $35 | Includes dressing |
| Injection | $15 | Per injection |
| IV Therapy | $50 | Per session |
| ECG | $30 | Per test |
| X-Ray | $75 | Per view |

## Insurance Processing

### Coverage Checks
```python
def check_insurance_coverage(patient, services):
    if not patient.get('insurance_provider'):
        return {'covered': False, 'reason': 'No insurance'}

    provider = patient['insurance_provider']
    policy = patient['insurance_policy_number']

    # Apply coverage rules
    # (Would integrate with insurance portal)
```

### Auto-Approval Thresholds
| Total | Approval Required |
|-------|-----------------|
| <$100 | Auto (if enabled) |
| $100-$500 | Manager approval |
| >$500 | Director approval |

## Success Criteria
- [ ] Invoice created in Odoo
- [ ] Correct patient linked
- [ ] All items included
- [ ] Amount calculated correctly
- [ ] Insurance applied if applicable
- [ ] Dashboard.md updated with invoice details

## Error Handling
| Error | Action |
|-------|--------|
| Patient not found | Halt, log error, notify human |
| Invoice amount $0 | Halt, verify service items |
| Duplicate invoice detected | Flag for review, don't create |
| Insurance validation fails | Create full-price invoice, flag for review |

## Approval Workflow
```
Pending_Approval/invoice-{patient}-{date}.md
    ↓ (Human reviews and approves)
Approved/invoice-{patient}-{date}.md
    ↓ (Ralph executes)
Done/invoice-{patient}-{date}.md
```

## Related Skills
- `healthcare-records` - Visit must be recorded first
- `business-audit` - Invoice appears in audit reports
- `vault-reader` - Access approval status
