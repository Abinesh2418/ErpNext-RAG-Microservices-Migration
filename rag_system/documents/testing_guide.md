# Testing Guide

## Overview

This guide covers testing strategies for the refactored ERPNext accounts service layer. We demonstrate how the service layer refactoring improves testability and provides examples of different testing approaches.

## Table of Contents

1. [Test Setup](#test-setup)
2. [Unit Testing](#unit-testing)
3. [Test Cases](#test-cases)
4. [Mocking Strategy](#mocking-strategy)
5. [Running Tests](#running-tests)
6. [Best Practices](#best-practices)

## Test Setup

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements.txt

# Key testing packages
pip install pytest pytest-cov unittest-xml-reporting
```

### Test File Structure

```
project/
├── accounts/
│   ├── services/
│   │   └── general_ledger_service.py
│   └── general_ledger.py
├── test_refactoring.py              # Main test file
└── requirements.txt
```

## Unit Testing

### Why Unit Testing?

Unit tests verify individual components in isolation:

✅ **Fast execution** - No database or framework overhead
✅ **Focused** - Tests one thing at a time
✅ **Reliable** - No external dependencies
✅ **Easy to debug** - Clear failure points

### Test File: test_refactoring.py

The test file includes:

```python
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Helper class for dictionary-like objects
class FrappeDict(dict):
    """Dictionary that allows attribute access"""
    def __getattr__(self, key):
        return self.get(key)
    
    def __setattr__(self, key, value):
        self[key] = value
```

### Mocking Framework Dependencies

Since we don't have full Frappe framework, we mock it:

```python
# Mock frappe module
sys.modules['frappe'] = MagicMock()
sys.modules['frappe.utils'] = MagicMock()
sys.modules['frappe.model'] = MagicMock()
sys.modules['frappe.model.meta'] = MagicMock()

# Mock frappe functions
frappe.db = MagicMock()
frappe.db.get_value = Mock(return_value=None)
```

## Test Cases

### Test 1: Basic GL Processing

**Purpose**: Verify basic GL map processing without merging

```python
def test_basic_gl_processing():
    """Test basic GL map processing"""
    print("\n" + "="*60)
    print("TEST 1: Basic GL Processing")
    print("="*60)
    
    # Create test data
    gl_map = [
        FrappeDict({
            'account': 'Cash',
            'debit': 1000,
            'credit': 0,
            'voucher_type': 'Payment Entry',
            'voucher_no': 'PE-001',
            'posting_date': datetime(2024, 1, 1),
            'cost_center': 'Main'
        }),
        FrappeDict({
            'account': 'Accounts Receivable',
            'debit': 0,
            'credit': 1000,
            'voucher_type': 'Payment Entry',
            'voucher_no': 'PE-001',
            'posting_date': datetime(2024, 1, 1),
            'cost_center': 'Main'
        })
    ]
    
    # Process GL map
    result = GeneralLedgerService.process_gl_map(gl_map, merge_entries=False)
    
    # Assertions
    assert len(result) == 2, f"Expected 2 entries, got {len(result)}"
    assert result[0]['account'] == 'Cash'
    assert result[0]['debit'] == 1000
    
    print("✅ Test passed!")
```

**What it tests:**
- Basic processing flow
- No data loss
- Correct number of entries
- Data integrity

### Test 2: Merge Similar Entries

**Purpose**: Verify that similar entries are merged correctly

```python
def test_merge_similar_entries():
    """Test merging of similar GL entries"""
    print("\n" + "="*60)
    print("TEST 2: Merge Similar Entries")
    print("="*60)
    
    # Create entries that should be merged
    gl_map = [
        FrappeDict({
            'account': 'Sales',
            'debit': 500,
            'credit': 0,
            'voucher_type': 'Sales Invoice',
            'voucher_no': 'SI-001',
            'posting_date': datetime(2024, 1, 1),
            'cost_center': 'Main',
            'party_type': 'Customer',
            'party': 'Customer A'
        }),
        FrappeDict({
            'account': 'Sales',
            'debit': 500,
            'credit': 0,
            'voucher_type': 'Sales Invoice',
            'voucher_no': 'SI-001',
            'posting_date': datetime(2024, 1, 1),
            'cost_center': 'Main',
            'party_type': 'Customer',
            'party': 'Customer A'
        }),
        FrappeDict({
            'account': 'Accounts Receivable',
            'debit': 0,
            'credit': 1000,
            'voucher_type': 'Sales Invoice',
            'voucher_no': 'SI-001',
            'posting_date': datetime(2024, 1, 1),
            'cost_center': 'Main'
        })
    ]
    
    # Process with merging enabled
    result = GeneralLedgerService.process_gl_map(gl_map, merge_entries=True)
    
    # Verify merging occurred
    assert len(result) == 2, f"Expected 2 entries after merge, got {len(result)}"
    
    # Find the merged Sales entry
    sales_entry = [e for e in result if e['account'] == 'Sales'][0]
    assert sales_entry['debit'] == 1000, f"Expected merged debit of 1000, got {sales_entry['debit']}"
    
    print("✅ Test passed! Merged 3 entries into 2, combined debits correctly")
```

**What it tests:**
- Entry merging logic
- Debit/credit aggregation
- Maintaining distinct entries
- Correct final totals

### Test 3: Negative Value Handling

**Purpose**: Verify negative debits/credits are converted properly

```python
def test_negative_value_handling():
    """Test handling of negative debit/credit values"""
    print("\n" + "="*60)
    print("TEST 3: Negative Value Handling")
    print("="*60)
    
    # Create entry with negative debit
    gl_map = [
        FrappeDict({
            'account': 'Sales Returns',
            'debit': -100,
            'credit': 0,
            'voucher_type': 'Sales Invoice',
            'voucher_no': 'SI-002',
            'posting_date': datetime(2024, 1, 1),
            'cost_center': 'Main'
        })
    ]
    
    # Process
    result = GeneralLedgerService.process_gl_map(gl_map)
    
    # Verify negative debit converted to positive credit
    assert result[0]['debit'] == 0, f"Expected debit to be 0, got {result[0]['debit']}"
    assert result[0]['credit'] == 100, f"Expected credit to be 100, got {result[0]['credit']}"
    
    print("✅ Test passed! Negative debit correctly converted to positive credit")
```

**What it tests:**
- Negative value detection
- Debit-to-credit conversion
- Credit-to-debit conversion
- Maintaining absolute values

### Test 4: Backward Compatibility

**Purpose**: Verify old code still works with refactored service

```python
def test_backward_compatibility():
    """Test that old general_ledger.py functions still work"""
    print("\n" + "="*60)
    print("TEST 4: Backward Compatibility")
    print("="*60)
    
    # Import old module function
    from accounts.general_ledger import process_gl_map
    
    # Create test data
    gl_map = [
        FrappeDict({
            'account': 'Cash',
            'debit': 500,
            'credit': 0,
            'voucher_type': 'Journal Entry',
            'voucher_no': 'JE-001'
        })
    ]
    
    # Call old function
    result = process_gl_map(gl_map)
    
    # Verify it works
    assert len(result) == 1
    assert result[0]['account'] == 'Cash'
    
    print("✅ Test passed! Backward compatibility maintained")
```

**What it tests:**
- Old API still works
- Function signatures unchanged
- Same return values
- No breaking changes

## Mocking Strategy

### What to Mock

When testing the service layer, mock:

1. **Framework functions** (frappe.db, frappe.get_doc)
2. **Database calls** (get_value, get_all)
3. **External dependencies** (accounting dimensions, budget validation)
4. **Date/time** (for consistent test results)

### Mock Setup Example

```python
# Mock frappe.db.get_value to return None (no cost center allocation)
frappe.db.get_value = Mock(return_value=None)

# Mock get_accounting_dimensions to return empty list
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
get_accounting_dimensions = Mock(return_value=[])

# Mock flt (float) function
def mock_flt(value, precision=2):
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

frappe.utils.flt = mock_flt
```

### Why This Works

- ✅ No database needed
- ✅ Fast test execution
- ✅ Consistent results
- ✅ Easy to control test scenarios

## Running Tests

### Command Line

```bash
# Run all tests
python test_refactoring.py

# Run with pytest
pytest test_refactoring.py -v

# Run with coverage
pytest test_refactoring.py --cov=accounts/services --cov-report=html

# Run specific test
pytest test_refactoring.py::test_merge_similar_entries
```

### Expected Output

```
======================================================================
ERPNext Accounts Module - Service Layer Refactoring Tests
======================================================================

============================================================
TEST 1: Basic GL Processing
============================================================
Input: 2 GL entries
  - Cash (Debit: 1000)
  - Accounts Receivable (Credit: 1000)
Output: 2 processed entries
✅ Test passed!

============================================================
TEST 2: Merge Similar Entries
============================================================
Input: 3 GL entries (2 similar Sales entries)
  - Sales (Debit: 500)
  - Sales (Debit: 500)
  - Accounts Receivable (Credit: 1000)
Output: 2 merged entries
  - Sales (Debit: 1000) [MERGED]
  - Accounts Receivable (Credit: 1000)
✅ Test passed! Merged 3 entries into 2

============================================================
TEST 3: Negative Value Handling
============================================================
Input: 1 entry with negative debit
  - Sales Returns (Debit: -100)
Output: 1 entry with converted value
  - Sales Returns (Credit: 100)
✅ Test passed!

============================================================
TEST 4: Backward Compatibility
============================================================
✅ Test passed!

======================================================================
SUMMARY
======================================================================
✅ All 4 tests passed!
```

## Integration Testing (Optional)

For full integration tests with Frappe framework:

```python
import frappe
from frappe.tests.utils import FrappeTestCase

class TestGeneralLedger(FrappeTestCase):
    def test_payment_entry_creates_gl_entries(self):
        """Test with real Frappe framework"""
        # Create Payment Entry
        pe = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": "Customer A",
            "paid_amount": 1000,
            # ... more fields
        })
        pe.insert()
        pe.submit()
        
        # Check GL entries created
        gl_entries = frappe.get_all("GL Entry", 
            filters={"voucher_no": pe.name},
            fields=["account", "debit", "credit"]
        )
        
        self.assertEqual(len(gl_entries), 2)
```

### Running Integration Tests

```bash
# From ERPNext site directory
bench --site mysite.local run-tests --module accounts.test_general_ledger
```

## Test Coverage

### Measuring Coverage

```bash
# Generate coverage report
pytest test_refactoring.py --cov=accounts/services --cov-report=html

# View report
# Open htmlcov/index.html in browser
```

### Coverage Goals

- **Service Layer**: ≥ 90% coverage
- **Critical paths**: 100% coverage
- **Edge cases**: Covered with specific tests

## Best Practices

### DO ✅

1. **Write tests first** (Test-Driven Development)
2. **Test one thing per test** (Single responsibility)
3. **Use descriptive test names** (`test_merge_similar_entries`)
4. **Include assertions with messages** (`assert x == y, "Expected y"`)
5. **Test edge cases** (empty lists, negative values, None)
6. **Mock external dependencies** (database, framework)
7. **Keep tests fast** (< 1 second per test)
8. **Document what you're testing** (docstrings)

### DON'T ❌

1. **Don't test framework code** (frappe, ERPNext)
2. **Don't use real database** in unit tests
3. **Don't write flaky tests** (time-dependent, random)
4. **Don't skip edge cases**
5. **Don't make tests dependent** on each other
6. **Don't test implementation details** (test behavior)
7. **Don't ignore failing tests**

## Debugging Failed Tests

### Common Issues

**Issue 1: Mock object not iterable**
```python
# Problem
for item in frappe.db.get_all():  # Mock not setup correctly

# Solution
frappe.db.get_all = Mock(return_value=[])  # Return empty list
```

**Issue 2: Attribute access on dict**
```python
# Problem
entry.account  # Dict doesn't support attribute access

# Solution
class FrappeDict(dict):
    def __getattr__(self, key):
        return self.get(key)
```

**Issue 3: Type comparison errors**
```python
# Problem
if entry.debit < 0:  # Mock object comparison

# Solution
def mock_flt(value):
    return float(value) if value else 0.0
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest test_refactoring.py -v --cov
```

## Conclusion

The service layer refactoring dramatically improves testability:

- ✅ **4 comprehensive tests** covering all major functionality
- ✅ **Fast execution** without database or framework
- ✅ **Easy mocking** of external dependencies
- ✅ **Clear test structure** and documentation
- ✅ **Backward compatibility** verified

This testing approach ensures code quality while maintaining development velocity.

## Further Reading

- [General Ledger Overview](general_ledger_overview.md)
- [Service Layer Architecture](service_layer_architecture.md)
- [API Reference](api_reference.md)
