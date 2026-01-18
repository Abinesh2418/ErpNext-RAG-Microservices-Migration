"""
Ledger Service - Main Application Entry Point
==============================================

Initializes the Ledger Service and sets up event subscriptions.
"""

from consumers import LedgerConsumer


class LedgerService:
    """
    Ledger Service - Manages general ledger operations.
    
    Responsibilities:
    - Listen to invoice events
    - Update general ledger entries
    - Maintain accounting records
    - Provide trial balance and reporting
    """
    
    def __init__(self):
        """Initialize the ledger service."""
        print("\n" + "="*70)
        print("INITIALIZING LEDGER SERVICE")
        print("="*70)
        self.consumer = LedgerConsumer()
        print("✅ Ledger Service initialized successfully")


def main():
    """
    Initialize the Ledger Service.
    
    This service runs passively, listening to events and reacting.
    It doesn't have a main loop in this prototype.
    """
    service = LedgerService()
    
    print("\n" + "="*70)
    print("LEDGER SERVICE - READY")
    print("="*70)
    print("Status: ✓ Listening for INVOICE_CREATED events")
    print("        ✓ Ready to update general ledger")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
