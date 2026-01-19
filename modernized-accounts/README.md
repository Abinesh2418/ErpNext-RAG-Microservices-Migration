# AI-Assisted Migration: ERP Accounts Module to Microservices + Event-Driven Architecture

## 📋 Overview

This prototype demonstrates the architectural transformation of a **monolithic ERPNext Accounts module** into a **microservices-based, event-driven system**.

### Legacy System (Monolithic)
```
┌─────────────────────────────────────┐
│    ERPNext Accounts Module          │
│  (All logic in one place)           │
├─────────────────────────────────────┤
│ • Invoice Creation                  │
│ • Tax Calculation (inline)          │
│ • Ledger Updates (inline)           │
│ • Party Management                  │
│ • Reporting                         │
└─────────────────────────────────────┘
```

### Modern System (Microservices + Event-Driven)
```
┌────────────────────────────────────────────────────────────────┐
│                    Event Bus (Message Queue)                   │
├────────────────────────────────────────────────────────────────┤
│  Topics: INVOICE_CREATED, INVOICE_UPDATED, ...                │
└────────────────────────────────────────────────────────────────┘
    ↑              ↑                  ↑
    │ publishes    │ publishes        │ publishes
    │              │                  │
    │              │                  │
┌───────────┐  ┌──────────┐       ┌──────────┐
│  Invoice  │  │  Ledger  │       │   Tax    │
│ Service   │  │ Service  │       │ Service  │
└───────────┘  └──────────┘       └──────────┘
    │                │               │
    └────┬───────────┴───────────┬───┘
         │ subscribes to         │
    ┌────v─────────────────────v─┐
    │   Event Bus (In-Memory)     │
    │  • Events flow asynchronously│
    │  • Loose coupling            │
    │  • Scalable independently    │
    └─────────────────────────────┘
```

## 🎯 Project Structure

```
modernized-accounts/
│
├── README.md (this file)
├── SETUP_GUIDE.md
├── simple_demo.py
│
├── event_bus/
│   ├── event_bus.py        # In-memory event system
│   └── README.md           # Event bus documentation
│
├── invoice-service/
│   ├── app.py             # Invoice service entry point
│   ├── invoice_logic.py   # Core invoice logic (extracted)
│   ├── events.py          # Event constants
│   └── README.md          # Service documentation
│
├── ledger-service/
│   ├── app.py             # Ledger service entry point
│   ├── ledger_logic.py    # Core ledger logic (extracted)
│   ├── consumers.py       # Event handlers
│   └── README.md          # Service documentation
│
└── tax-service/
    ├── app.py             # Tax service entry point
    ├── tax_logic.py       # Core tax logic (extracted)
    ├── consumers.py       # Event handlers
    └── README.md          # Service documentation
```

## 🔄 Data Flow: Complete Invoice Processing

### Step-by-Step Flow

```
1. INVOICE CREATION
   ┌──────────────────────┐
   │ Invoice Service      │
   │ • Receives invoice   │
   │ • Validates data     │
   │ • Creates invoice    │
   │ • Generates ID       │
   └─────────┬────────────┘
             │
             v
   2. EMIT EVENT: INVOICE_CREATED
      ┌──────────────────────────────┐
      │ Event Bus                    │
      │ publish("INVOICE_CREATED",   │
      │   {invoice_id, customer,     │
      │    items, subtotal, ...})    │
      └──────┬───────────────────────┘
             │
        ┌────┴────────┬─────────────┐
        │             │             │
        v             v             v
   3.1 LEDGER      3.2 TAX       (More services)
      SERVICE       SERVICE
      
   3.1 LEDGER SERVICE PROCESSES
       ┌──────────────────────────┐
       │ Event Received:          │
       │ INVOICE_CREATED          │
       │                          │
       │ • Subscribe handler runs │
       │ • Validates invoice      │
       │ • Creates GL entries     │
       │   - Debit: AR            │
       │   - Credit: Revenue      │
       │ • Updates balances       │
       │ • Prints trial balance   │
       └──────────────────────────┘

   3.2 TAX SERVICE PROCESSES
       ┌──────────────────────────┐
       │ Event Received:          │
       │ INVOICE_CREATED          │
       │                          │
       │ • Subscribe handler runs │
       │ • Validates invoice      │
       │ • Analyzes items         │
       │ • Applies tax rules      │
       │ • Calculates tax         │
       │ • Generates report       │
       └──────────────────────────┘

4. COMPLETE
   All services have processed the invoice independently
   and asynchronously. The system is now consistent.
```

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- No external dependencies (everything built from scratch for this prototype)

### Running the Demo

#### Quick Start

Simply run the demo script:

```bash
cd modernized-accounts
python simple_demo.py
```

This will:
1. Initialize all microservices
2. Create a sample invoice
3. Trigger the event-driven flow
4. Show results from all services

#### Run Individual Services

You can also test individual services:

1. **Initialize the Event Bus** (runs in each service):
   ```bash
   cd event_bus/
   python event_bus.py
   ```

2. **Start Ledger Service** (in a new terminal):
   ```bash
   cd ledger-service/
   python app.py
   ```

3. **Start Tax Service** (in a new terminal):
   ```bash
   cd tax-service/
   python app.py
   ```

4. **Trigger Invoice Creation** (in a new terminal):
   ```bash
   cd invoice-service/
   python app.py
   ```

## 🏗️ Architecture Principles

### 1. **Microservices**
- Each service has a single responsibility
- Services can be deployed independently
- Services communicate via events only

### 2. **Event-Driven**
- Asynchronous communication through events
- Loose coupling between services
- Publish-Subscribe pattern

### 3. **Separation of Concerns**
```
Invoice Service     → Handles invoice creation
Ledger Service      → Handles accounting records
Tax Service         → Handles tax calculations
Event Bus           → Handles messaging
```

### 4. **Scalability**
- Each service can be scaled independently
- No direct dependencies between services
- New services can be added without modifying existing ones

## 📊 Legacy → Modern Mapping

| Responsibility | Legacy System | Modern System |
|---|---|---|
| Invoice Creation | `general_ledger.py` | Invoice Service |
| Tax Calculation | `taxes_and_totals.py` | Tax Service |
| Ledger Updates | `general_ledger.py` | Ledger Service |
| Party Management | `party.py` | (Future: Party Service) |
| Communication | Function calls (sync) | Event Bus (async) |

### Code Extracted From

**Invoice Service**
- ✓ `accounts/general_ledger.py`: Invoice ID generation, validation
- ✓ `accounts/controllers/selling_controller.py`: Item validation

**Ledger Service**
- ✓ `accounts/general_ledger.py`: Ledger entry creation, balance tracking
- ✓ `accounts/deferred_revenue.py`: Revenue recognition concepts
- ✓ `accounts/party.py`: Customer-to-account mapping

**Tax Service**
- ✓ `accounts/controllers/taxes_and_totals.py`: Tax calculation logic
- ✓ `accounts/controllers/selling_controller.py`: Item-level taxation

## 🎓 Key Concepts Demonstrated

### Event Publishing
When an invoice is created, the service publishes an event:
```python
publish("INVOICE_CREATED", {
    "invoice_id": "INV-001",
    "customer": "ACME Corp",
    "total": 7000.00
})
```

### Event Subscription
Other services subscribe and react:
```python
subscribe("INVOICE_CREATED", handle_invoice_created)

def handle_invoice_created(invoice_data):
    print(f"Processing invoice: {invoice_data['invoice_id']}")
    # Do work here
```

## 🔮 Future Enhancements

### Production-Ready Implementation

**Replace In-Memory Event Bus with:**
- Apache Kafka (distributed event streaming)
- RabbitMQ (message broker)
- AWS SNS/SQS (cloud-native)
- Redis (simpler use case)

**Add Services:**
- Party Service (customer management)
- Payment Service (payment processing)
- Audit Service (compliance tracking)
- Reporting Service (financial reports)

**Add Infrastructure:**
- Docker containerization
- Kubernetes orchestration
- API Gateway
- Service Discovery
- Distributed Tracing
- Health Checks & Monitoring

**Add Persistence:**
- PostgreSQL/MongoDB (per-service databases)
- Event Store (for event sourcing)
- CQRS (Command Query Responsibility Segregation)

## 📚 Documentation

Each service has its own README:
- [event_bus/README.md](event_bus/README.md) - Event bus architecture
- [invoice-service/README.md](invoice-service/README.md) - Invoice service details
- [ledger-service/README.md](ledger-service/README.md) - Ledger service details
- [tax-service/README.md](tax-service/README.md) - Tax service details

## 🧪 Testing

Each service can be tested independently:

```python
# Test Invoice Service
from invoice-service.invoice_logic import InvoiceLogic
logic = InvoiceLogic()
invoice = logic.create_invoice({
    "customer": "Test Corp",
    "items": [{"description": "Test", "qty": 1, "rate": 100}]
})
assert invoice['invoice_id'].startswith('INV-')

# Test Ledger Service
from ledger-service.ledger_logic import LedgerLogic
ledger = LedgerLogic()
ledger.update_ledger(invoice)
assert len(ledger.ledger_entries) == 2  # AR + Revenue entries

# Test Tax Service
from tax-service.tax_logic import TaxLogic
tax = TaxLogic()
tax_calc = tax.calculate_tax(invoice)
assert tax_calc['total_tax'] > 0
```

## 📋 Prototype Limitations

This prototype focuses on **architecture clarity** and is NOT production-ready:

| Aspect | Prototype | Production |
|---|---|---|
| Event Bus | In-memory (lost on restart) | Persistent message broker |
| Storage | In-memory dict | Database |
| Scaling | Single process | Multiple instances |
| Monitoring | Print statements | Distributed tracing |
| Error Handling | Basic try-catch | Comprehensive + Retry logic |
| Security | None | Authentication + Authorization |
| API | Direct imports | REST/gRPC APIs |
| Deployment | Direct Python | Docker + Kubernetes |

## 📬 Contact

For any queries or suggestions, feel free to reach out:

- 🏆 **LeetCode:** [leetcode.com/u/abinesh_06](https://leetcode.com/u/abinesh_06/)
- 📧 **Email:** abineshbalasubramaniyam@gmail.com
- 💼 **LinkedIn:** [linkedin.com/in/abiineshh](https://www.linkedin.com/in/abiineshh/)
- 🐙 **GitHub:** [github.com/Abinesh2418](https://github.com/Abinesh2418)

