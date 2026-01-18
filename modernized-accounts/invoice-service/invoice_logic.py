from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json
import os


class InvoiceLogic:
    """
    Core invoice business logic from legacy system.
    
    Extracted from: Erpnext-Refactoring/accounts/general_ledger.py
    Focuses on invoice creation and validation.
    """
    
    def __init__(self):
        """Initialize the invoice logic."""
        self.invoices_store = {}  # Simple in-memory storage
        self._log_file = os.path.join(os.path.dirname(__file__), 'invoice_logs.json')
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new invoice.
        """
        
        # Validate required fields
        self._validate_invoice_data(invoice_data)
        
        # Generate invoice ID
        invoice_id = self._generate_invoice_id()
        
        # Calculate totals
        subtotal = self._calculate_subtotal(invoice_data.get("items", []))
        
        # Create invoice object
        invoice = {
            "invoice_id": invoice_id,
            "customer": invoice_data.get("customer"),
            "items": invoice_data.get("items", []),
            "subtotal": subtotal,
            "tax": 0.0,  # Tax calculation delegated to Tax Service
            "total": subtotal,  # Will be updated after tax calculation
            "due_date": invoice_data.get("due_date"),
            "notes": invoice_data.get("notes", ""),
            "status": "DRAFT",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store invoice (in production, this would be a database)
        self.invoices_store[invoice_id] = invoice
        
        # Save to JSON log
        self._save_to_log(invoice)
        
        print(f"✅ Invoice created successfully")
        print(f"   Invoice ID: {invoice['invoice_id']}")
        print(f"   Customer: {invoice['customer']}")
        print(f"   Subtotal: ${invoice['subtotal']:.2f}")
        
        return invoice
    
    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an invoice by ID.
        
        Args:
            invoice_id (str): The invoice ID
            
        Returns:
            Dict or None: The invoice data, or None if not found
        """
        return self.invoices_store.get(invoice_id)
    
    def list_invoices(self) -> list:
        """
        Get all invoices.
        
        Returns:
            List: All invoices in the system
        """
        return list(self.invoices_store.values())
    
    def _validate_invoice_data(self, invoice_data: Dict[str, Any]) -> None:
        """
        Validate invoice data structure.
        
        Raises:
            ValueError: If required fields are missing or invalid
        """
        if "customer" not in invoice_data or not invoice_data["customer"]:
            raise ValueError("Invoice must have a customer name")
        
        if "items" not in invoice_data or not invoice_data["items"]:
            raise ValueError("Invoice must have at least one item")
        
        for item in invoice_data["items"]:
            if "description" not in item:
                raise ValueError("Each item must have a description")
            if "qty" not in item or item["qty"] <= 0:
                raise ValueError("Each item must have a valid quantity")
            if "rate" not in item or item["rate"] < 0:
                raise ValueError("Each item must have a valid rate")
    
    def _calculate_subtotal(self, items: list) -> float:
        """
        Calculate the subtotal from line items.
        
        Args:
            items (list): List of invoice line items
            
        Returns:
            float: The subtotal amount
        """
        subtotal = 0.0
        for item in items:
            subtotal += item["qty"] * item["rate"]
        return round(subtotal, 2)
    
    def _generate_invoice_id(self) -> str:
        """
        Generate a unique invoice ID.
        
        Returns:
            str: A unique invoice identifier
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_part = str(uuid.uuid4())[:5].upper()
        return f"INV-{timestamp}-{unique_part}"
    
    def update_invoice_tax(self, invoice_id: str, tax_amount: float) -> None:
        """
        Update invoice with tax information.
        
        Called by Tax Service after tax calculation.
        
        Args:
            invoice_id (str): The invoice ID
            tax_amount (float): The calculated tax amount
        """
        if invoice_id in self.invoices_store:
            invoice = self.invoices_store[invoice_id]
            invoice["tax"] = round(tax_amount, 2)
            invoice["total"] = round(invoice["subtotal"] + tax_amount, 2)
            invoice["updated_at"] = datetime.now().isoformat()
            print(f"   📝 Invoice {invoice_id} updated with tax: ${tax_amount:.2f}")
    
    def _save_to_log(self, invoice: Dict[str, Any]) -> None:
        """
        Save invoice to JSON log file.
        
        Args:
            invoice (Dict[str, Any]): The invoice to save
        """
        try:
            # Read existing logs
            if os.path.exists(self._log_file):
                with open(self._log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Append new invoice
            logs.append(invoice)
            
            # Write back to file
            with open(self._log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Could not save invoice log to file: {e}")
