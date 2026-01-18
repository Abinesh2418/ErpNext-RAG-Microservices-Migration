# Event Bus - Microservice Communication Layer

## Overview

The **Event Bus** is the core communication mechanism for the microservices architecture. It provides a simple, in-memory event system that allows services to communicate asynchronously through events.

## Architecture

```
┌─────────────────────────────────────────┐
│         Event Bus (In-Memory)           │
│  - Manages event subscriptions          │
│  - Routes events to subscribers         │
│  - Maintains event log                  │
└─────────────────────────────────────────┘
         ↑              ↑              ↑
         │              │              │
    Publisher     Subscribers    Event Log
```

## Key Concepts

### Event Publishing
When a service (e.g., Invoice Service) creates an entity, it **publishes** an event:
```python
publish("INVOICE_CREATED", {
    "invoice_id": "INV001",
    "customer": "ACME Corp",
    "amount": 10000.00
})
```

### Event Subscription
Other services (e.g., Ledger Service, Tax Service) **subscribe** to events:
```python
subscribe("INVOICE_CREATED", handle_invoice_created)
```

When the event is published, all subscribed handlers are called automatically.

## API Reference

### `subscribe(event_name, handler)`
Register a handler function to listen for an event.

**Parameters:**
- `event_name` (str): Name of the event to listen for
- `handler` (Callable): Function to call when the event is published

**Example:**
```python
from event_bus.event_bus import subscribe

def on_invoice_created(payload):
    print(f"Invoice created: {payload['invoice_id']}")

subscribe("INVOICE_CREATED", on_invoice_created)
```

### `publish(event_name, payload)`
Emit an event to all registered subscribers.

**Parameters:**
- `event_name` (str): Name of the event to publish
- `payload` (Dict): Data associated with the event

**Example:**
```python
from event_bus.event_bus import publish

publish("INVOICE_CREATED", {
    "invoice_id": "INV001",
    "amount": 5000.00
})
```

## Why Event Bus?

### Decoupling
Services don't need to know about each other directly. They only know about events.

### Scalability
New services can subscribe to events without modifying existing code.

### Asynchronicity
Services can process events independently.

## Production Considerations

In a production system, the Event Bus would be replaced by:
- **Apache Kafka**: Distributed event streaming
- **RabbitMQ**: Message broker with reliability
- **AWS SNS/SQS**: Cloud-based messaging
- **Redis**: Pub/Sub for simpler use cases

These systems provide:
- ✓ Persistence (events survive service restarts)
- ✓ Scalability (handle millions of events)
- ✓ Reliability (guaranteed delivery)
- ✓ Multi-instance support (distributed systems)
