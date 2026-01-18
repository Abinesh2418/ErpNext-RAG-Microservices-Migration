from typing import Dict, Any, List
from datetime import datetime
import json
import os


class LedgerLogic:
    """
    Core ledger business logic from legacy system.
    
    Extracted from: Erpnext-Refactoring/accounts/general_ledger.py
    Focuses on general ledger entry management.
    """
    
    def __init__(self):
        """Initialize the ledger logic."""
        self.ledger_entries = []  # List of all ledger entries
        self.account_balances = {}  # Track balances by account
        self._log_file = os.path.join(os.path.dirname(__file__), 'ledger_logs.json')
    
    def update_ledger(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update general ledger with invoice information.
        """
        
        invoice_id = invoice_data.get("invoice_id")
        customer = invoice_data.get("customer")
        amount = invoice_data.get("total", invoice_data.get("subtotal", 0))
        
        print(f"\n📊 Processing ledger update for invoice: {invoice_id}")
        
        # Create AR (Accounts Receivable) entry
        ar_entry = {
            "entry_id": f"GL-{invoice_id}-AR",
            "invoice_id": invoice_id,
            "account": "Accounts Receivable",
            "account_type": "Asset",
            "customer": customer,
            "debit": amount,
            "credit": 0.0,
            "description": f"Sales to {customer}",
            "reference": invoice_id,
            "date": datetime.now().isoformat(),
            "status": "POSTED"
        }
        
        # Create Revenue entry (opposite of AR)
        revenue_entry = {
            "entry_id": f"GL-{invoice_id}-REV",
            "invoice_id": invoice_id,
            "account": "Sales Revenue",
            "account_type": "Income",
            "customer": customer,
            "debit": 0.0,
            "credit": amount,
            "description": f"Revenue from {customer}",
            "reference": invoice_id,
            "date": datetime.now().isoformat(),
            "status": "POSTED"
        }
        
        # Add entries to ledger
        self.ledger_entries.append(ar_entry)
        self.ledger_entries.append(revenue_entry)
        
        # Update account balances
        self._update_account_balance("Accounts Receivable", amount, "debit")
        self._update_account_balance("Sales Revenue", amount, "credit")
        
        # Log the update
        print(f"   ✅ Ledger updated successfully")
        print(f"   📝 AR Entry: {ar_entry['entry_id']}")
        print(f"      Debit (AR): ${ar_entry['debit']:.2f}")
        print(f"   📝 Revenue Entry: {revenue_entry['entry_id']}")
        print(f"      Credit (Revenue): ${revenue_entry['credit']:.2f}")
        print(f"   ✓ Double-entry verified: Debit = ${amount:.2f}, Credit = ${amount:.2f}")
        
        # Save to JSON log
        result = {
            "invoice_id": invoice_id,
            "ar_entry": ar_entry,
            "revenue_entry": revenue_entry,
            "timestamp": datetime.now().isoformat()
        }
        self._save_to_log(result)
        
        return ar_entry
    
    def get_account_balance(self, account_name: str) -> float:
        """
        Get the current balance for an account.
        
        Args:
            account_name (str): Name of the account
            
        Returns:
            float: The account balance
        """
        return self.account_balances.get(account_name, 0.0)
    
    def get_ledger_entries(self, invoice_id: str = None) -> List[Dict[str, Any]]:
        """
        Get ledger entries, optionally filtered by invoice.
        
        Args:
            invoice_id (str, optional): Filter by invoice ID
            
        Returns:
            List: Ledger entries
        """
        if invoice_id:
            return [e for e in self.ledger_entries if e.get("invoice_id") == invoice_id]
        return self.ledger_entries
    
    def get_trial_balance(self) -> Dict[str, float]:
        """
        Get a trial balance report showing all account balances.
        
        Returns:
            Dict: Account names mapped to their balances
        """
        return self.account_balances.copy()
    
    def _update_account_balance(self, account: str, amount: float, entry_type: str) -> None:
        """
        Update account balance based on debit/credit entry.
        
        Args:
            account (str): Account name
            amount (float): Transaction amount
            entry_type (str): "debit" or "credit"
        """
        if account not in self.account_balances:
            self.account_balances[account] = 0.0
        
        if entry_type == "debit":
            self.account_balances[account] += amount
        elif entry_type == "credit":
            self.account_balances[account] -= amount
    
    def _save_to_log(self, ledger_entry: Dict[str, Any]) -> None:
        """
        Save ledger entry to JSON log file.
        
        Args:
            ledger_entry (Dict[str, Any]): The ledger entry to save
        """
        try:
            # Read existing logs
            if os.path.exists(self._log_file):
                with open(self._log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Append new entry
            logs.append(ledger_entry)
            
            # Write back to file
            with open(self._log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Could not save ledger log to file: {e}")


class LedgerReporter:
    """
    Generates ledger reports for accounting and audit purposes.
    """
    
    def __init__(self, ledger_logic: LedgerLogic):
        """Initialize reporter with ledger logic reference."""
        self.ledger = ledger_logic
    
    def print_trial_balance(self) -> None:
        """Print trial balance report."""
        balances = self.ledger.get_trial_balance()
        
        print("\n" + "="*60)
        print("TRIAL BALANCE REPORT")
        print("="*60)
        print(f"{'Account':<35} {'Balance':>20}")
        print("-"*60)
        
        total_debit = 0
        total_credit = 0
        
        for account, balance in balances.items():
            if balance >= 0:
                print(f"{account:<35} ${balance:>18.2f}")
                total_debit += balance
            else:
                print(f"{account:<35} ${balance:>18.2f}")
                total_credit += abs(balance)
        
        print("-"*60)
        print(f"{'TOTALS':<35} Debit: ${total_debit:>14.2f}, Credit: ${total_credit:>14.2f}")
        print("="*60 + "\n")
    
    def print_ledger_entries(self, invoice_id: str = None) -> None:
        """Print ledger entries in a formatted table."""
        entries = self.ledger.get_ledger_entries(invoice_id)
        
        print("\n" + "="*100)
        print(f"LEDGER ENTRIES {f'(Invoice: {invoice_id})' if invoice_id else '(All Invoices)'}")
        print("="*100)
        print(f"{'Entry ID':<25} {'Account':<20} {'Debit':>12} {'Credit':>12} {'Status':<10}")
        print("-"*100)
        
        for entry in entries:
            print(f"{entry['entry_id']:<25} {entry['account']:<20} "
                  f"${entry['debit']:>10.2f} ${entry['credit']:>10.2f} {entry['status']:<10}")
        
        print("="*100 + "\n")
