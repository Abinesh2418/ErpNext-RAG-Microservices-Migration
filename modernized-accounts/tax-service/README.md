# Tax Service

## Overview

The **Tax Service** is responsible for calculating and managing taxes on invoices. It subscribes to invoice events and automatically computes applicable taxes based on configured tax rules and item classifications.

## Responsibility

This service owns:
- ✓ Tax rate management
- ✓ Tax calculation logic
- ✓ Tax rule engine
- ✓ Tax exemptions
- ✓ Tax reporting

This service does NOT own:
- ✗ Invoice creation (Invoice Service)
- ✗ Ledger updates (Ledger Service)
- ✗ Payment processing
- ✗ Compliance/Audit (separate service)

## Architecture

```
┌────────────────────────────────────────────────┐
│         Tax Service (app.py)                   │
│                                                │
│  ┌─────────────────────────────────────────┐  │
│  │  TaxConsumer (consumers.py)             │  │
│  │  - _handle_invoice_created()            │  │
│  │  - _register_handlers()                 │  │
│  └─────────────────────────────────────────┘  │
│              ↓ subscribes                      │
│  ┌─────────────────────────────────────────┐  │
│  │  Event Bus (listen)                     │  │
│  │  Event: INVOICE_CREATED                 │  │
│  └─────────────────────────────────────────┘  │
│              ↓ triggers                       │
│  ┌─────────────────────────────────────────┐  │
│  │  TaxLogic (tax_logic.py)                │  │
│  │  - calculate_tax()                      │  │
│  │  - _calculate_itemwise_tax()            │  │
│  │  - apply_tax_exemption()                │  │
│  └─────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

## Events Consumed

### INVOICE_CREATED
Triggers tax calculation when invoice is created.

**Payload (from Invoice Service):**
```json
{
    "invoice_id": "INV-20260117-ABC12",
    "customer": "ACME Corporation",
    "items": [
        {
            "description": "Professional Services",
            "qty": 10,
            "rate": 500.00
        },
        {
            "description": "Premium Widget",
            "qty": 5,
            "rate": 200.00
        }
    ],
    "subtotal": 6000.00,
    "tax": 0.00,
    "total": 6000.00
}
```

**Action:** Calculates and returns taxes:
1. Analyzes each item
2. Applies appropriate tax rate
3. Creates tax calculation record
4. Logs tax summary

## Tax Rules

The Tax Service applies different tax rates based on item classification:

| Category | Tax Rate | Applies To |
|----------|----------|-----------|
| Luxury Items | 15% | Items with keywords: "luxury", "premium", "high-end" |
| Goods & Services | 10% | General GST rate |
| Basic Items | 5% | Default rate |

### Example Tax Calculation

**Invoice:**
```
Item 1: Professional Services (qty: 10, rate: $500)
        Subtotal: $5,000 → Tax (10% GST): $500 → Total: $5,500

Item 2: Premium Widget (qty: 5, rate: $200)
        Subtotal: $1,000 → Tax (15% Luxury): $150 → Total: $1,150

Invoice Total: $6,000
Total Tax: $650
Total with Tax: $6,650
```

## Core Business Logic Extracted

### From: `taxes_and_totals.py`
- Tax rate calculation algorithms
- Tax rule engine
- Tax type classification

### From: `selling_controller.py`
- Item-level tax determination

### From: `party.py`
- Customer tax exemption status

## Tax Calculation Structure

Each tax calculation contains:
```python
{
    "tax_id": "TAX-INV-XYZ",
    "invoice_id": "INV-XYZ",
    "subtotal": 6000.00,
    "items_breakdown": [
        {
            "description": "Professional Services",
            "subtotal": 5000.00,
            "tax_rate": 0.10,
            "tax_type": "GST",
            "tax": 500.00,
            "total_with_tax": 5500.00
        }
    ],
    "total_tax": 650.00,
    "total_with_tax": 6650.00,
    "tax_type": "GST/Sales Tax",
    "calculated_at": "2026-01-17T...",
    "status": "CALCULATED"
}
```

## API Reference

### `TaxService` (app.py)

Entry point for the service. Automatically initializes event subscriptions.

### `TaxConsumer.get_tax_calculation(invoice_id)`

Retrieve tax calculation for an invoice.

**Returns:**
```python
{
    "tax_id": "TAX-INV-001",
    "invoice_id": "INV-001",
    "subtotal": 6000.00,
    "total_tax": 650.00,
    "total_with_tax": 6650.00,
    "status": "CALCULATED"
}
```

### `TaxConsumer.get_all_calculations()`

Get all tax calculations.

## Reports

### Tax Summary Report

Shows tax calculations across all invoices.

```
TAX SUMMARY REPORT
─────────────────────────────────────────────────────
Invoice              Subtotal          Tax        Total
─────────────────────────────────────────────────────
INV-20260117-ABC    $6,000.00      $650.00   $6,650.00
INV-20260117-DEF    $5,000.00      $500.00   $5,500.00
─────────────────────────────────────────────────────
TOTALS             $11,000.00    $1,150.00  $12,150.00
```

## Tax Exemptions

Some customers or invoices may qualify for tax exemptions. In the future, this could be enhanced with:
- Exemption rules by customer type
- Government exemption certificates
- Audit logging of exemptions

## Why Separate?

In the monolithic system, tax calculations happened inline during invoice creation. This new service provides:

1. **Flexibility**: Tax rules can be updated without touching invoice logic
2. **Scalability**: Tax calculations don't block invoice creation
3. **Reusability**: Tax engine can be used by other services (quotes, proposals, etc.)
4. **Testability**: Complex tax logic can be tested independently
5. **Auditability**: All tax calculations are isolated and traceable

## Running the Service

```python
from app import TaxService

# Initialize service (automatically subscribes to events)
service = TaxService()

# When invoices are created, this service automatically calculates taxes
```

## Integration Example

See [../README.md](../README.md) for a complete end-to-end flow example.
