import sys
import os
import importlib.util

# Setup paths
demo_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(demo_dir, 'event_bus'))
sys.path.insert(0, os.path.join(demo_dir, 'invoice-service'))
sys.path.insert(0, os.path.join(demo_dir, 'ledger-service'))
sys.path.insert(0, os.path.join(demo_dir, 'tax-service'))


def load_module(module_name, filepath):
    """Helper to load a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


print("\n" + "="*80)
print(" "*20 + "MICROSERVICES ARCHITECTURE DEMO")
print("="*80 + "\n")

# Step 1: Load Event Bus
print("1️⃣  Initializing Event Bus...")
event_bus_mod = load_module('event_bus_mod', 
                             os.path.join(demo_dir, 'event_bus', 'event_bus.py'))
get_event_bus = event_bus_mod.get_event_bus
publish = event_bus_mod.publish

event_bus = get_event_bus()
print("   ✓ Event Bus ready\n")

# Step 2: Initialize Services (they register event handlers)
print("2️⃣  Initializing Microservices (Ledger & Tax Services)...")

# Load Ledger Service modules
ledger_logic_mod = load_module('ledger_logic_mod',
                               os.path.join(demo_dir, 'ledger-service', 'ledger_logic.py'))
ledger_consumers_mod = load_module('ledger_consumers_mod',
                                   os.path.join(demo_dir, 'ledger-service', 'consumers.py'))

# Load Tax Service modules
tax_logic_mod = load_module('tax_logic_mod',
                            os.path.join(demo_dir, 'tax-service', 'tax_logic.py'))
tax_consumers_mod = load_module('tax_consumers_mod',
                                os.path.join(demo_dir, 'tax-service', 'consumers.py'))

# Create service instances (automatically subscribes to events)
ledger_service = ledger_consumers_mod.LedgerConsumer()
tax_service = tax_consumers_mod.TaxConsumer()

print("   ✓ All services registered and listening for events\n")

# Step 3: Create an invoice (this triggers the event chain)
print("3️⃣  Creating an invoice (triggers automatic event processing)...\n")

# Load Invoice Service
invoice_logic_mod = load_module('invoice_logic_mod',
                                os.path.join(demo_dir, 'invoice-service', 'invoice_logic.py'))

invoice_logic = invoice_logic_mod.InvoiceLogic()

# Invoice data
invoice_data = {
    "customer": "ACME Corporation",
    "items": [
        {"description": "Professional Services", "qty": 10, "rate": 500.00},
        {"description": "Premium Software License", "qty": 5, "rate": 200.00},
        {"description": "Hardware Equipment", "qty": 2, "rate": 1500.00},
    ],
    "due_date": "2026-02-28",
    "notes": "Thank you for your business!"
}

# Create the invoice
invoice = invoice_logic.create_invoice(invoice_data)

# Publish the event (this triggers Ledger and Tax services)
print("\n📨 Publishing INVOICE_CREATED event...")
publish("INVOICE_CREATED", invoice)

# Step 4: Summary
print("\n" + "="*80)
print("✅ DEMO COMPLETE")
print("="*80)

print(f"""
WHAT HAPPENED:
══════════════════════════════════════════════════════════════════

1. Invoice Service
   • Created invoice: {invoice['invoice_id']}
   • Customer: {invoice['customer']}
   • Subtotal: ${invoice['subtotal']:.2f}
   • Status: {invoice['status']}
   ✓ Published INVOICE_CREATED event

2. Ledger Service (Event Consumer)
   • Received INVOICE_CREATED event
   • Created double-entry ledger records:
     - Debit: Accounts Receivable ${invoice['total']:.2f}
     - Credit: Sales Revenue ${invoice['total']:.2f}
   ✓ General ledger updated

3. Tax Service (Event Consumer)
   • Received INVOICE_CREATED event
   • Analyzed {len(invoice['items'])} line items
   • Applied tax rules (GST/Luxury Tax)
   • Calculated itemized taxes
   ✓ Tax calculation completed

4. Event Bus
   • Received 1 publish request
   • Routed event to 2 subscribers
   • Asynchronous processing complete
   ✓ Event distribution successful


KEY INSIGHTS:
══════════════════════════════════════════════════════════════════

✓ Services are LOOSELY COUPLED
✓ Services process INDEPENDENTLY
✓ Services are EASILY EXTENSIBLE
✓ FAULT ISOLATION is improved
✓ SCALABILITY is enhanced

NEXT STEPS:
══════════════════════════════════════════════════════════════════

📖 Read the documentation:
   • README.md - Complete architecture overview
   • event_bus/README.md - Event system details
   • invoice-service/README.md - Invoice service design
   • ledger-service/README.md - Ledger service design
   • tax-service/README.md - Tax service design

🔬 Explore the code:
   • Modify invoice data
   • Add custom tax rules
   • Create new event types
   • Add more services 

ARCHITECTURE SUMMARY:
══════════════════════════════════════════════════════════════════

Legacy (Monolithic)          Modern (Microservices)
───────────────────         ──────────────────────
general_ledger.py      →    Invoice + Ledger Services
taxes_and_totals.py    →    Tax Service
Tight coupling         →    Loose coupling via events
Synchronous            →    Asynchronous
Single deployment      →    Independent deployment


Thank you for exploring this microservices prototype! 🎉
""")

print("="*80 + "\n")
