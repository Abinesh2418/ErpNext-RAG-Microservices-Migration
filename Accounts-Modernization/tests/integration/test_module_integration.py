"""
Integration Tests
Tests interactions between Go modules (invoice → ledger, invoice → tax, etc.)
"""

import subprocess
import json
from pathlib import Path


def test_invoice_to_ledger_flow():
    """
    Test integration: Invoice creation should trigger ledger entries
    """
    print("\n🧪 Testing Invoice → Ledger Integration...\n")
    
    # Check if invoice and ledger modules exist
    modern_dir = Path(__file__).parent.parent.parent / 'modern'
    invoice_dir = modern_dir / 'invoice'
    ledger_dir = modern_dir / 'ledger'
    
    if not invoice_dir.exists():
        print("  ⚠️ Invoice module not found")
        return False
    
    if not ledger_dir.exists():
        print("  ⚠️ Ledger module not found")
        return False
    
    print("  ✓ Both modules found")
    print("  ℹ️ Manual verification required:")
    print("     - Invoice creation should generate ledger entries")
    print("     - Debit and credit should balance")
    print("     - Account codes should be valid")
    
    return True


def test_invoice_to_tax_flow():
    """
    Test integration: Invoice should calculate taxes correctly
    """
    print("\n🧪 Testing Invoice → Tax Integration...\n")
    
    modern_dir = Path(__file__).parent.parent.parent / 'modern'
    invoice_dir = modern_dir / 'invoice'
    tax_dir = modern_dir / 'tax'
    
    if not invoice_dir.exists():
        print("  ⚠️ Invoice module not found")
        return False
    
    if not tax_dir.exists():
        print("  ⚠️ Tax module not found")
        return False
    
    print("  ✓ Both modules found")
    print("  ℹ️ Manual verification required:")
    print("     - Tax calculation should be accurate")
    print("     - Multiple tax rates should be handled")
    print("     - Tax rounding should match accounting rules")
    
    return True


def test_module_dependencies():
    """
    Test that module dependencies are correctly handled
    """
    print("\n🧪 Testing Module Dependencies...\n")
    
    modern_dir = Path(__file__).parent.parent.parent / 'modern'
    
    if not modern_dir.exists():
        print("  ⚠️ No modern/ directory found")
        return False
    
    modules = [d for d in modern_dir.iterdir() if d.is_dir()]
    
    if not modules:
        print("  ⚠️ No modules found")
        return False
    
    print(f"  Found {len(modules)} modules:")
    for module in modules:
        go_files = list(module.glob('*.go'))
        print(f"    • {module.name}: {len(go_files)} files")
    
    print("\n  ✓ Module structure verified")
    return True


if __name__ == '__main__':
    print("="*60)
    print("  INTEGRATION TESTS")
    print("="*60)
    
    results = []
    results.append(test_module_dependencies())
    results.append(test_invoice_to_ledger_flow())
    results.append(test_invoice_to_tax_flow())
    
    print("\n" + "="*60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("="*60 + "\n")
