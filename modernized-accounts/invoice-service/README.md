# Invoice Service

## Overview

The **Invoice Service** is responsible for managing the creation and basic lifecycle of invoices. It extracts core invoice logic from the monolithic ERPNext system and exposes it as an independent microservice.

## Responsibility

This service owns:
- ✓ Invoice creation
- ✓ Invoice data storage (in-memory for prototype)
- ✓ Invoice validation
- ✓ Event emission for invoice lifecycle changes

This service does NOT own:
- ✗ Tax calculation (delegated to Tax Service)
- ✗ General ledger entries (delegated to Ledger Service)
- ✗ Payment processing
- ✗ Invoice templates/formatting

## Architecture

```
┌──────────────────────────────────────────┐
│        Invoice Service (app.py)          │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  InvoiceService (app.py)         │   │
│  │  - create_invoice()              │   │
│  │  - get_invoice()                 │   │
│  │  - list_invoices()               │   │
│  └──────────────────────────────────┘   │
│           ↓                              │
│  ┌──────────────────────────────────┐   │
│  │  InvoiceLogic (invoice_logic.py) │   │
│  │  - _validate_invoice_data()      │   │
│  │  - _calculate_subtotal()         │   │
│  │  - _generate_invoice_id()        │   │
│  └──────────────────────────────────┘   │
│           ↓                              │
│  ┌──────────────────────────────────┐   │
│  │  Event Bus (publish)             │   │
│  │  Emits: INVOICE_CREATED          │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
```

## Events Published

### INVOICE_CREATED
Emitted when a new invoice is successfully created.

**Event Payload:**
```json
{
    "invoice_id": "INV-20260117-ABC12",
    "customer": "ACME Corporation",
    "items": [
        {
            "description": "Professional Services",
            "qty": 10,
            "rate": 500.00
        }
    ],
    "subtotal": 7000.00,
    "tax": 0.00,
    "total": 7000.00,
    "due_date": "2026-02-17",
    "status": "DRAFT",
    "created_at": "2026-01-17T10:30:45.123456"
}
```

**Subscribers:**
- Ledger Service: Updates general ledger with the invoice entry
- Tax Service: Calculates and applies taxes

## Core Business Logic Extracted

### From: `general_ledger.py`
- Invoice ID generation strategy
- Invoice validation rules
- Subtotal calculation logic

### From: `selling_controller.py`
- Customer validation
- Item line validation

## API Reference

### `InvoiceService.create_invoice(invoice_data)`

Creates a new invoice and emits INVOICE_CREATED event.

**Input:**
```python
{
    "customer": "ACME Corp",
    "items": [
        {
            "description": "Widget A",
            "qty": 10,
            "rate": 100.00
        }
    ],
    "due_date": "2026-02-17",  # Optional
    "notes": "Custom notes"     # Optional
}
```

**Output:**
```python
{
    "invoice_id": "INV-20260117-XYZ99",
    "customer": "ACME Corp",
    "items": [...],
    "subtotal": 1000.00,
    "tax": 0.00,
    "total": 1000.00,
    "status": "DRAFT",
    "created_at": "2026-01-17T...",
    "updated_at": "2026-01-17T..."
}
```

**Errors:**
- `ValueError`: If customer is missing
- `ValueError`: If items list is empty or invalid

## Why Separate?

In the monolithic system, invoice creation, tax calculation, and ledger updates all happened in a single transaction. This created tight coupling and made it hard to:

1. **Scale independently**: Tax calculations are now done in a separate service
2. **Reuse logic**: Other services can trigger ledger updates without creating invoices
3. **Test in isolation**: Each service can be tested independently
4. **Deploy independently**: Changes to tax rules don't require invoice service redeploy

## Running the Service

```python
from app import InvoiceService

service = InvoiceService()
invoice = service.create_invoice({
    "customer": "ACME Corp",
    "items": [
        {"description": "Service", "qty": 1, "rate": 5000.00}
    ]
})
```

Or run the demo:
```bash
python app.py
```
