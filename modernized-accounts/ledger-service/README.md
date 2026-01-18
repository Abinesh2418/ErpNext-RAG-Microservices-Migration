# Ledger Service

## Overview

The **Ledger Service** is responsible for maintaining the general ledger and accounting records. It subscribes to invoice events and automatically updates the ledger with appropriate debit and credit entries.

## Responsibility

This service owns:
- ✓ General ledger entry creation
- ✓ Account balance tracking
- ✓ Double-entry bookkeeping verification
- ✓ Trial balance reporting

This service does NOT own:
- ✗ Invoice creation (Invoice Service)
- ✗ Tax calculation (Tax Service)
- ✗ Payment processing
- ✗ Customer management

## Architecture

```
┌────────────────────────────────────────────────┐
│         Ledger Service (app.py)                │
│                                                │
│  ┌─────────────────────────────────────────┐  │
│  │  LedgerConsumer (consumers.py)          │  │
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
│  │  LedgerLogic (ledger_logic.py)          │  │
│  │  - update_ledger()                      │  │
│  │  - get_account_balance()                │  │
│  │  - _update_account_balance()            │  │
│  └─────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

## Events Consumed

### INVOICE_CREATED
Triggers ledger update when invoice is created.

**Payload (from Invoice Service):**
```json
{
    "invoice_id": "INV-20260117-ABC12",
    "customer": "ACME Corporation",
    "subtotal": 7000.00,
    "tax": 350.00,
    "total": 7350.00
}
```

**Action:** Creates accounting entries:
1. Debit: Accounts Receivable ($7350.00)
2. Credit: Sales Revenue ($7350.00)

## Core Business Logic Extracted

### From: `general_ledger.py`
- Ledger entry creation and posting
- Account balance tracking
- Double-entry bookkeeping rules
- Trial balance calculations

### From: `party.py`
- Customer-to-account mapping

### From: `deferred_revenue.py`
- Revenue recognition principles

## Ledger Entry Structure

Each ledger entry contains:
```python
{
    "entry_id": "GL-INV-XYZ-AR",           # Unique entry identifier
    "invoice_id": "INV-XYZ",               # Source invoice
    "account": "Accounts Receivable",      # Account name
    "account_type": "Asset",               # Type: Asset, Liability, Equity, Income, Expense
    "debit": 7350.00,                      # Debit amount (or 0)
    "credit": 0.0,                         # Credit amount (or 0)
    "description": "Sales to ACME Corp",   # Human-readable description
    "reference": "INV-XYZ",                # Reference document
    "date": "2026-01-17T...",             # Entry date
    "status": "POSTED"                     # Status: DRAFT, POSTED, REVERSED
}
```

## Double-Entry Bookkeeping

Every transaction must have:
- **Debit entries** (increase in assets or expenses)
- **Credit entries** (increase in liabilities, equity, or income)
- **Balance**: Total debits = Total credits

**Example for Invoice:**
```
INVOICE_CREATED: Total = $7350.00

Debit:  Accounts Receivable    $7350.00
Credit: Sales Revenue                     $7350.00
        ─────────────────────────────────
        Balance: $7350.00  =  $7350.00 ✓
```

## API Reference

### `LedgerService` (app.py)

Entry point for the service. Automatically initializes event subscriptions.

### `LedgerConsumer.get_ledger_entries(invoice_id=None)`

Retrieve ledger entries, optionally filtered by invoice.

**Returns:**
```python
[
    {
        "entry_id": "GL-INV-001-AR",
        "invoice_id": "INV-001",
        "account": "Accounts Receivable",
        "debit": 1000.00,
        "credit": 0.0
    },
    {
        "entry_id": "GL-INV-001-REV",
        "invoice_id": "INV-001",
        "account": "Sales Revenue",
        "debit": 0.0,
        "credit": 1000.00
    }
]
```

### `LedgerConsumer.get_trial_balance()`

Get current account balances.

**Returns:**
```python
{
    "Accounts Receivable": 15000.00,
    "Sales Revenue": -15000.00
}
```

## Reports

### Trial Balance Report

Shows all account balances at a point in time. Used to verify the general ledger's accuracy (debits should equal credits).

```
TRIAL BALANCE REPORT
─────────────────────────────────────────────────────
Account                              Balance
─────────────────────────────────────────────────────
Accounts Receivable                  $15,000.00
Sales Revenue                       -$15,000.00
─────────────────────────────────────────────────────
TOTALS                    Debit: $15,000.00, Credit: $15,000.00
```

## Why Separate?

In the monolithic system, ledger updates happened inline with invoice creation. This new service provides:

1. **Scalability**: Ledger updates don't block invoice creation
2. **Audit Trail**: All ledger operations are isolated and auditable
3. **Flexibility**: Can update multiple ledgers or add new ones without modifying invoice logic
4. **Resilience**: If ledger service fails, invoice still gets created (eventual consistency)
5. **Testing**: Ledger logic can be tested independently

## Running the Service

```python
from app import LedgerService

# Initialize service (automatically subscribes to events)
service = LedgerService()

# When invoices are created, this service automatically handles them
```

## Integration Example

See [../README.md](../README.md) for a complete end-to-end flow example.
