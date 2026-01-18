# SETUP GUIDE - Modernized Accounts Microservices

## 📦 Installation & Setup

### Step 1: Verify Structure

Make sure you have the following structure:

```
modernized-accounts/
├── README.md
├── SETUP_GUIDE.md
├── simple_demo.py
│
├── event_bus/
│   ├── __init__.py
│   ├── event_bus.py
│   └── README.md
│
├── invoice-service/
│   ├── __init__.py
│   ├── app.py
│   ├── invoice_logic.py
│   ├── events.py
│   └── README.md
│
├── ledger-service/
│   ├── __init__.py
│   ├── app.py
│   ├── ledger_logic.py
│   ├── consumers.py
│   └── README.md
│
└── tax-service/
    ├── __init__.py
    ├── app.py
    ├── tax_logic.py
    ├── consumers.py
    └── README.md
```

### Step 2: Run the Demo

```bash
cd modernized-accounts
python simple_demo.py
```

This demonstrates the complete event-driven flow in one script.

### Step 3: Explore Individual Services

**Invoice Service:**
```bash
cd invoice-service
python app.py
```

**Ledger Service:**
```bash
cd ledger-service
python app.py
```

**Tax Service:**
```bash
cd tax-service
python app.py
```

## 🎯 What Each Component Does

### Event Bus (`event_bus/`)
- **event_bus.py**: Core event system with subscribe() and publish() functions
- **README.md**: Architecture documentation

### Invoice Service (`invoice-service/`)
- **invoice_logic.py**: Core invoice creation logic extracted from ERPNext
- **events.py**: Event name constants (INVOICE_CREATED, etc.)
- **app.py**: Service entry point and demo
- **README.md**: Service documentation

### Ledger Service (`ledger-service/`)
- **ledger_logic.py**: General ledger management, double-entry bookkeeping
- **consumers.py**: Event handlers that subscribe to INVOICE_CREATED
- **app.py**: Service entry point
- **README.md**: Service documentation

### Tax Service (`tax-service/`)
- **tax_logic.py**: Tax calculation engine with itemized tax rates
- **consumers.py**: Event handlers that subscribe to INVOICE_CREATED
- **app.py**: Service entry point
- **README.md**: Service documentation

## 🔄 Flow Diagram

```
[Invoice Service]
      │
      │ (1) create_invoice()
      │
      ▼
[Invoice Created]
      │
      │ (2) publish("INVOICE_CREATED", {...})
      │
      ▼
[Event Bus]
      │
      ├────────────────┬───────────────┐
      ▼                ▼               ▼
[Ledger Service]  [Tax Service]  (More Services)
      │                │
      │ (3a)           │ (3b)
      │                │
      ▼                ▼
 Update Ledger    Calculate Tax
```

## 📚 Reading Order

1. **README.md** (root) - Overview and architecture
2. **event_bus/README.md** - Event-driven architecture explained
3. **invoice-service/README.md** - Invoice service details
4. **ledger-service/README.md** - Ledger service details
5. **tax-service/README.md** - Tax service details

## 🧪 Manual Testing

### Test 1: Create an Invoice

```python
import sys
import os
sys.path.insert(0, 'event_bus')
sys.path.insert(0, 'invoice-service')

from invoice_logic import InvoiceLogic

logic = InvoiceLogic()
invoice = logic.create_invoice({
    "customer": "Test Corp",
    "items": [
        {"description": "Widget", "qty": 5, "rate": 100.00}
    ]
})

print(f"Invoice ID: {invoice['invoice_id']}")
print(f"Total: ${invoice['total']}")
```

### Test 2: Event Publishing

```python
import sys
sys.path.insert(0, 'event_bus')

from event_bus import get_event_bus

bus = get_event_bus()

def handler(data):
    print(f"Received: {data}")

bus.subscribe("TEST", handler)
bus.publish("TEST", {"message": "Hello!"})
```

### Test 3: Ledger Update

```python
import sys
sys.path.insert(0, 'ledger-service')

from ledger_logic import LedgerLogic

ledger = LedgerLogic()
ledger.update_ledger({
    "invoice_id": "TEST-001",
    "customer": "Test Corp",
    "total": 500.00
})

print(f"Ledger entries: {len(ledger.ledger_entries)}")
print(f"Account balances: {ledger.get_trial_balance()}")
```

### Test 4: Tax Calculation

```python
import sys
sys.path.insert(0, 'tax-service')

from tax_logic import TaxLogic

tax = TaxLogic()
result = tax.calculate_tax({
    "invoice_id": "TEST-001",
    "items": [
        {"description": "Service", "qty": 10, "rate": 100.00}
    ],
    "subtotal": 1000.00
})

print(f"Tax: ${result['total_tax']}")
print(f"Total with tax: ${result['total_with_tax']}")
```

## 🐛 Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`, ensure you're in the correct directory and paths are set:

```python
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.getcwd(), 'event_bus'))
sys.path.insert(0, os.path.join(os.getcwd(), 'invoice-service'))
sys.path.insert(0, os.path.join(os.getcwd(), 'ledger-service'))
sys.path.insert(0, os.path.join(os.getcwd(), 'tax-service'))
```

### No Output

If you don't see output, ensure all services are initialized before creating an invoice.

### Event Not Received

Ensure services are initialized (which registers their event handlers) BEFORE publishing events.

## 🚀 Next Steps

1. **Understand the Flow**: Run `simple_demo.py` and follow the console output
2. **Read Documentation**: Each service has detailed README.md files
3. **Experiment**: Modify invoice data, add new tax rules, create custom reports
4. **Extend**: Add new services (Payment Service, Party Service, etc.)

## 📞 Support

- Check individual service README.md files for detailed documentation
- Review code comments in each .py file
- Experiment with the demo scripts

## ✅ Verification Checklist

- [ ] All folders created
- [ ] All Python files present
- [ ] `simple_demo.py` runs without errors
- [ ] Event Bus initializes
- [ ] Services subscribe to events
- [ ] Invoice creation triggers events
- [ ] Ledger updates automatically
- [ ] Tax calculation works

Congratulations! You've successfully set up a microservices prototype with event-driven architecture! 🎉
