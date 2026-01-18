"""
Invoice Service - Main Application Entry Point
===============================================

Initializes the invoice service and provides the main API for invoice creation.
This service is responsible for managing the invoice lifecycle and emitting events.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'event_bus'))

from invoice_logic import InvoiceLogic
from events import INVOICE_CREATED
from event_bus import publish


class InvoiceService:
    """
    Invoice Service - Manages invoice creation and lifecycle.
    
    Responsibilities:
    - Accept invoice creation requests
    - Create invoices using business logic
    - Publish INVOICE_CREATED events
    - Provide invoice data to other services
    """
    
    def __init__(self):
        """Initialize the invoice service with business logic."""
        self.logic = InvoiceLogic()
    
    def create_invoice(self, invoice_data):
        """
        Create a new invoice and emit the INVOICE_CREATED event.
        
        Args:
            invoice_data (dict): The invoice data
            
        Returns:
            dict: The created invoice
        """
        # Create the invoice using business logic
        invoice = self.logic.create_invoice(invoice_data)
        
        # Publish the event so other services can react
        print(f"\n📨 Emitting INVOICE_CREATED event...")
        publish(INVOICE_CREATED, invoice)
        
        return invoice
    
    def get_invoice(self, invoice_id):
        """Get an invoice by ID."""
        return self.logic.get_invoice(invoice_id)
    
    def list_invoices(self):
        """Get all invoices."""
        return self.logic.list_invoices()


def main():
    """
    Demo: Create a sample invoice and emit the INVOICE_CREATED event.
    
    This demonstrates the basic invoice creation flow.
    """
    print("\n" + "="*70)
    print("INVOICE SERVICE - DEMO")
    print("="*70)
    
    # Initialize the service
    service = InvoiceService()
    
    # Sample invoice data
    invoice_data = {
        "customer": "ACME Corporation",
        "items": [
            {"description": "Professional Services", "qty": 10, "rate": 500.00},
            {"description": "Software License", "qty": 5, "rate": 200.00},
            {"description": "Hardware", "qty": 2, "rate": 1500.00}
        ],
        "due_date": "2026-02-17",
        "notes": "Payment terms: Net 30"
    }
    
    print("\n📋 Creating invoice...")
    print(f"   Customer: {invoice_data['customer']}")
    print(f"   Items: {len(invoice_data['items'])}")
    
    # Create the invoice (this also publishes the event)
    invoice = service.create_invoice(invoice_data)
    
    print("\n✅ Invoice creation flow completed!")
    print(f"   Invoice ID: {invoice['invoice_id']}")
    print(f"   Status: {invoice['status']}")


if __name__ == "__main__":
    main()
