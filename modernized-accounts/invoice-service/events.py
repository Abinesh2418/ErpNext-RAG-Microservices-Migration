"""
Invoice Service - Event Constants
==================================

Central location for all event names used in the microservices architecture.
This ensures consistency across services and makes it easy to discover available events.
"""

# Invoice Service Events
INVOICE_CREATED = "INVOICE_CREATED"
INVOICE_UPDATED = "INVOICE_UPDATED"
INVOICE_CANCELLED = "INVOICE_CANCELLED"
INVOICE_SUBMITTED = "INVOICE_SUBMITTED"

# Other potential events (for future expansion)
PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
INVOICE_OVERDUE = "INVOICE_OVERDUE"

# Event metadata
ALL_EVENTS = [
    INVOICE_CREATED,
    INVOICE_UPDATED,
    INVOICE_CANCELLED,
    INVOICE_SUBMITTED,
]

EVENT_DESCRIPTIONS = {
    INVOICE_CREATED: "Fired when a new invoice is created in the system",
    INVOICE_UPDATED: "Fired when an existing invoice is updated",
    INVOICE_CANCELLED: "Fired when an invoice is cancelled",
    INVOICE_SUBMITTED: "Fired when an invoice is submitted for approval",
}
