from typing import Dict, Any, List
from datetime import datetime
import json
import os


class TaxLogic:
    """
    Core tax calculation business logic from legacy system.
    
    Extracted from: Erpnext-Refactoring/controllers/taxes_and_totals.py
    Focuses on tax calculation and application.
    """
    
    # Tax rates and rules (in production, these would come from configuration)
    DEFAULT_TAX_RATE = 0.05  # 5% sales tax
    GST_RATE = 0.10  # 10% GST (Goods and Services Tax)
    LUXURY_TAX_RATE = 0.15  # 15% for luxury items
    
    # Luxury items classification
    LUXURY_ITEMS = ["luxury", "premium", "high-end"]
    
    def __init__(self):
        """Initialize the tax logic."""
        self.tax_calculations = []
    
    def calculate_tax(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate tax for an invoice.
        """
        
        invoice_id = invoice_data.get("invoice_id")
        items = invoice_data.get("items", [])
        subtotal = invoice_data.get("subtotal", 0)
        
        print(f"\n💰 Calculating tax for invoice: {invoice_id}")
        
        # Calculate tax for each item
        items_tax_breakdown = self._calculate_itemwise_tax(items)
        
        # Calculate total tax
        total_tax = sum(item_calc["tax"] for item_calc in items_tax_breakdown)
        total_tax = round(total_tax, 2)
        
        # Create tax calculation record
        tax_calc = {
            "tax_id": f"TAX-{invoice_id}",
            "invoice_id": invoice_id,
            "subtotal": subtotal,
            "tax_rate": "Variable (per-item)",
            "items_breakdown": items_tax_breakdown,
            "total_tax": total_tax,
            "total_with_tax": round(subtotal + total_tax, 2),
            "tax_type": "GST/Sales Tax",
            "calculated_at": datetime.now().isoformat(),
            "status": "CALCULATED"
        }
        
        # Store calculation
        self.tax_calculations.append(tax_calc)
        
        # Log the calculation
        print(f"   ✅ Tax calculated successfully")
        print(f"   📊 Subtotal: ${subtotal:.2f}")
        print(f"   📊 Total Tax: ${total_tax:.2f}")
        print(f"   📊 Total with Tax: ${tax_calc['total_with_tax']:.2f}")
        
        # Print item breakdown
        self._print_tax_breakdown(items_tax_breakdown)
        
        # Save to JSON log
        self._save_to_log(tax_calc)
        
        return tax_calc
    
    def _calculate_itemwise_tax(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate tax for each line item.
        
        Different items may have different tax rates based on their category.
        
        Args:
            items (List): List of invoice items
            
        Returns:
            List: Tax calculation for each item
        """
        breakdown = []
        
        for item in items:
            description = item.get("description", "").lower()
            qty = item.get("qty", 0)
            rate = item.get("rate", 0)
            item_subtotal = qty * rate
            
            # Determine tax rate based on item classification
            if any(luxury_keyword in description for luxury_keyword in self.LUXURY_ITEMS):
                tax_rate = self.LUXURY_TAX_RATE
                tax_type = "Luxury Tax"
            else:
                # Default to GST
                tax_rate = self.GST_RATE
                tax_type = "GST"
            
            item_tax = round(item_subtotal * tax_rate, 2)
            
            breakdown.append({
                "description": item.get("description"),
                "qty": qty,
                "rate": rate,
                "subtotal": item_subtotal,
                "tax_rate": tax_rate,
                "tax_type": tax_type,
                "tax": item_tax,
                "total_with_tax": round(item_subtotal + item_tax, 2)
            })
        
        return breakdown
    
    def _print_tax_breakdown(self, breakdown: List[Dict[str, Any]]) -> None:
        """
        Print a formatted tax breakdown.
        
        Args:
            breakdown (List): Tax breakdown data
        """
        print(f"\n   📋 Tax Breakdown by Item:")
        print(f"   {'-'*80}")
        for item in breakdown:
            print(f"      • {item['description']:<30} | Tax: ${item['tax']:>8.2f} ({item['tax_type']})")
        print(f"   {'-'*80}")
    
    def _save_to_log(self, tax_calculation: Dict[str, Any]) -> None:
        """
        Save tax calculation to JSON log file.
        
        Args:
            tax_calculation (Dict[str, Any]): The tax calculation to save
        """
        try:
            # Read existing logs
            if os.path.exists(self._log_file):
                with open(self._log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Append new calculation
            logs.append(tax_calculation)
            
            # Write back to file
            with open(self._log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Could not save tax log to file: {e}")
    
    def apply_tax_exemption(self, invoice_id: str, exemption_reason: str) -> Dict[str, Any]:
        """
        Apply tax exemption to an invoice.
        
        In production, this would check authorization before applying exemptions.
        
        Args:
            invoice_id (str): The invoice ID
            exemption_reason (str): Reason for exemption
            
        Returns:
            Dict: Updated tax calculation with exemption
        """
        # Find the tax calculation
        for tax_calc in self.tax_calculations:
            if tax_calc["invoice_id"] == invoice_id:
                tax_calc["total_tax"] = 0.0
                tax_calc["total_with_tax"] = tax_calc["subtotal"]
                tax_calc["status"] = "EXEMPTED"
                tax_calc["exemption_reason"] = exemption_reason
                print(f"✅ Tax exemption applied: {exemption_reason}")
                return tax_calc
        
        raise ValueError(f"Tax calculation not found for invoice {invoice_id}")
    
    def get_tax_calculation(self, invoice_id: str) -> Dict[str, Any]:
        """
        Get tax calculation for an invoice.
        
        Args:
            invoice_id (str): The invoice ID
            
        Returns:
            Dict: Tax calculation details
        """
        for tax_calc in self.tax_calculations:
            if tax_calc["invoice_id"] == invoice_id:
                return tax_calc
        return None
    
    def get_all_calculations(self) -> List[Dict[str, Any]]:
        """
        Get all tax calculations.
        
        Returns:
            List: All tax calculations
        """
        return self.tax_calculations.copy()


class TaxReporter:
    """
    Generates tax-related reports and summaries.
    """
    
    def __init__(self, tax_logic: TaxLogic):
        """Initialize reporter with tax logic reference."""
        self.tax_logic = tax_logic
    
    def print_tax_summary(self) -> None:
        """Print a summary of all tax calculations."""
        calculations = self.tax_logic.get_all_calculations()
        
        print("\n" + "="*80)
        print("TAX SUMMARY REPORT")
        print("="*80)
        print(f"{'Invoice':<20} {'Subtotal':>12} {'Tax':>12} {'Total':>12} {'Status':<12}")
        print("-"*80)
        
        total_subtotal = 0
        total_tax = 0
        total_amount = 0
        
        for calc in calculations:
            print(f"{calc['invoice_id']:<20} ${calc['subtotal']:>10.2f} "
                  f"${calc['total_tax']:>10.2f} ${calc['total_with_tax']:>10.2f} {calc['status']:<12}")
            total_subtotal += calc['subtotal']
            total_tax += calc['total_tax']
            total_amount += calc['total_with_tax']
        
        print("-"*80)
        print(f"{'TOTALS':<20} ${total_subtotal:>10.2f} ${total_tax:>10.2f} ${total_amount:>10.2f}")
        print("="*80 + "\n")
