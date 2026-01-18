import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'event_bus'))

from tax_logic import TaxLogic, TaxReporter
from event_bus import subscribe, publish


class TaxConsumer:
    """
    Event consumer for the Tax Service.
    
    Subscribes to invoice events, calculates taxes, and updates the invoice
    with tax information.
    """
    
    def __init__(self):
        """Initialize the consumer and register event handlers."""
        self.tax_logic = TaxLogic()
        self.reporter = TaxReporter(self.tax_logic)
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register event handlers with the event bus."""
        print("\n🔗 Tax Service - Registering event handlers...")
        subscribe("INVOICE_CREATED", self._handle_invoice_created)
        print("   ✓ Handler registered for: INVOICE_CREATED")
    
    def _handle_invoice_created(self, invoice_data: dict) -> None:
        """
        Handle INVOICE_CREATED event.
        
        This is the main business logic execution point for the Tax Service.
        When an invoice is created, this handler calculates taxes automatically.
        
        Args:
            invoice_data (dict): Invoice data from the INVOICE_CREATED event
        """
        print("\n" + "="*70)
        print("⚡ TAX SERVICE - INVOICE_CREATED EVENT RECEIVED")
        print("="*70)
        
        try:
            # Calculate tax for the invoice
            tax_calculation = self.tax_logic.calculate_tax(invoice_data)
            
            # Emit a TAX_CALCULATED event for other services
            # (In this prototype, we just log it)
            print(f"\n📨 Tax calculation complete")
            print(f"   Tax ID: {tax_calculation['tax_id']}")
            print(f"   Tax Amount: ${tax_calculation['total_tax']:.2f}")
            
            # Show tax summary
            self.reporter.print_tax_summary()
            
        except Exception as e:
            print(f"❌ Error handling INVOICE_CREATED event: {e}")
    
    def get_tax_calculation(self, invoice_id: str) -> dict:
        """Get tax calculation for an invoice."""
        return self.tax_logic.get_tax_calculation(invoice_id)
    
    def get_all_calculations(self) -> list:
        """Get all tax calculations."""
        return self.tax_logic.get_all_calculations()
