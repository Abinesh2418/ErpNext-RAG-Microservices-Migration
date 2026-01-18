"""
Tax Service - Main Application Entry Point
============================================

Initializes the Tax Service and sets up event subscriptions.
"""

from consumers import TaxConsumer


class TaxService:
    """
    Tax Service - Manages tax calculation and reporting.
    
    Responsibilities:
    - Calculate taxes on invoices
    - Apply tax rules and exemptions
    - Generate tax reports
    """
    
    def __init__(self):
        """Initialize the tax service."""
        print("\n" + "="*70)
        print("INITIALIZING TAX SERVICE")
        print("="*70)
        self.consumer = TaxConsumer()
        print("✅ Tax Service initialized successfully")


def main():
    """
    Initialize the Tax Service.
    
    This service runs passively, listening to events and reacting.
    It doesn't have a main loop in this prototype.
    """
    service = TaxService()
    
    print("\n" + "="*70)
    print("TAX SERVICE - READY")
    print("="*70)
    print("Status: ✓ Listening for INVOICE_CREATED events")
    print("        ✓ Ready to calculate taxes")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
