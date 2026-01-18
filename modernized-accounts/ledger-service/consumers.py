import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'event_bus'))

from ledger_logic import LedgerLogic, LedgerReporter
from event_bus import subscribe


class LedgerConsumer:
    """
    Event consumer for the Ledger Service.
    
    Subscribes to invoice events and updates the general ledger accordingly.
    """
    
    def __init__(self):
        """Initialize the consumer and register event handlers."""
        self.ledger_logic = LedgerLogic()
        self.reporter = LedgerReporter(self.ledger_logic)
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register event handlers with the event bus."""
        print("\n🔗 Ledger Service - Registering event handlers...")
        subscribe("INVOICE_CREATED", self._handle_invoice_created)
        print("   ✓ Handler registered for: INVOICE_CREATED")
    
    def _handle_invoice_created(self, invoice_data: dict) -> None:
        """
        Handle INVOICE_CREATED event.
        
        This is the main business logic execution point for the Ledger Service.
        When an invoice is created in another service, this handler is called
        automatically by the event bus.
        
        Args:
            invoice_data (dict): Invoice data from the INVOICE_CREATED event
        """
        print("\n" + "="*70)
        print("⚡ LEDGER SERVICE - INVOICE_CREATED EVENT RECEIVED")
        print("="*70)
        
        try:
            # Update the ledger with the invoice information
            self.ledger_logic.update_ledger(invoice_data)
            
            # Optionally show the trial balance
            self.reporter.print_trial_balance()
            
        except Exception as e:
            print(f"❌ Error handling INVOICE_CREATED event: {e}")
    
    def get_ledger_entries(self, invoice_id: str = None) -> list:
        """Get ledger entries."""
        return self.ledger_logic.get_ledger_entries(invoice_id)
    
    def get_trial_balance(self) -> dict:
        """Get trial balance."""
        return self.ledger_logic.get_trial_balance()
