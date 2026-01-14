# API Reference

## GeneralLedgerService Class

Complete API documentation for the `GeneralLedgerService` class in the refactored accounts module.

## Table of Contents

1. [Class Overview](#class-overview)
2. [Public Methods](#public-methods)
3. [Private Methods](#private-methods)
4. [Data Structures](#data-structures)
5. [Usage Examples](#usage-examples)
6. [Error Handling](#error-handling)

## Class Overview

### Location

```python
from erpnext.accounts.services.general_ledger_service import GeneralLedgerService
```

### Description

The `GeneralLedgerService` class provides a service layer for General Ledger operations in ERPNext. It encapsulates business logic for processing GL entries, including cost center distribution, entry merging, and negative value handling.

### Class Definition

```python
class GeneralLedgerService:
    """
    Service class for General Ledger operations.
    
    This class provides a service layer for processing GL entries,
    helping to decouple business logic from direct database operations
    and improving testability and maintainability.
    """
```

## Public Methods

### process_gl_map

Main method for processing General Ledger Map entries.

#### Signature

```python
@staticmethod
def process_gl_map(gl_map, merge_entries=True, precision=None, from_repost=False):
    """
    Process General Ledger Map entries.
    
    Args:
        gl_map (list): List of GL entry dictionaries
        merge_entries (bool): Whether to merge similar entries (default: True)
        precision (int): Decimal precision for calculations (default: None)
        from_repost (bool): Whether called from reposting process (default: False)
        
    Returns:
        list: Processed GL map entries
    """
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `gl_map` | list | Yes | - | List of GL entry dictionaries containing transaction data |
| `merge_entries` | bool | No | True | Whether to merge similar entries to reduce redundancy |
| `precision` | int | No | None | Decimal precision for financial calculations |
| `from_repost` | bool | No | False | Flag indicating if called from GL reposting process |

#### Returns

**Type**: `list`

Returns a processed list of GL entry dictionaries with:
- Cost center allocation applied
- Similar entries merged (if enabled)
- Negative values converted to opposite side
- All business rules enforced

#### Processing Steps

1. **Skip Empty Maps**: Returns empty list if input is empty
2. **Cost Center Distribution**: Distributes entries based on allocation percentages
3. **Entry Merging**: Combines similar entries if `merge_entries=True`
4. **Negative Handling**: Converts negative debits to credits and vice versa

#### Example

```python
from erpnext.accounts.services.general_ledger_service import GeneralLedgerService

# Prepare GL entries
gl_map = [
    {
        'account': 'Cash',
        'debit': 1000,
        'credit': 0,
        'voucher_type': 'Payment Entry',
        'voucher_no': 'PE-001',
        'cost_center': 'Main'
    },
    {
        'account': 'Accounts Receivable',
        'debit': 0,
        'credit': 1000,
        'voucher_type': 'Payment Entry',
        'voucher_no': 'PE-001',
        'cost_center': 'Main'
    }
]

# Process GL map
processed_entries = GeneralLedgerService.process_gl_map(
    gl_map,
    merge_entries=True,
    precision=2
)

# Use processed entries
for entry in processed_entries:
    print(f"{entry['account']}: Debit={entry['debit']}, Credit={entry['credit']}")
```

#### Special Cases

**Period Closing Voucher**: Cost center distribution is skipped for Period Closing Vouchers as they handle allocation differently.

```python
if gl_map[0].voucher_type != "Period Closing Voucher":
    # Apply cost center distribution
```

## Private Methods

Private methods are internal implementation details. They are not meant to be called directly but are documented for understanding the internal workflow.

### _distribute_gl_based_on_cost_center_allocation

Distributes GL entries based on cost center allocation percentages.

#### Signature

```python
@staticmethod
def _distribute_gl_based_on_cost_center_allocation(gl_map, precision=None, from_repost=False):
    """
    Distribute GL entries based on cost center allocation percentages.
    
    Args:
        gl_map (list): List of GL entry dictionaries
        precision (int): Decimal precision for calculations
        from_repost (bool): Whether called from reposting
        
    Returns:
        list: GL map with entries distributed across cost centers
    """
```

#### How It Works

1. Queries cost center allocation data from database
2. For each entry with allocation:
   - Calculates proportional amounts based on percentages
   - Creates new entries for each cost center
   - Removes original entry
3. Returns expanded GL map with distributed entries

#### Example

**Input:**
```python
[
    {'account': 'Sales', 'debit': 1000, 'cost_center': 'Main'}
]
```

**Cost Center Allocation:**
- Main → Branch A: 60%
- Main → Branch B: 40%

**Output:**
```python
[
    {'account': 'Sales', 'debit': 600, 'cost_center': 'Branch A'},
    {'account': 'Sales', 'debit': 400, 'cost_center': 'Branch B'}
]
```

### _merge_similar_entries

Merges GL entries that have the same key properties.

#### Signature

```python
@staticmethod
def _merge_similar_entries(gl_map, precision=None):
    """
    Merge GL entries with identical merge keys.
    
    Args:
        gl_map (list): List of GL entry dictionaries
        precision (int): Decimal precision for calculations
        
    Returns:
        list: GL map with similar entries merged
    """
```

#### Merge Criteria

Entries are merged if they have identical:
- Account
- Party Type & Party
- Against
- Cost Center
- Against Voucher Type & Number
- All accounting dimensions

#### Merge Logic

```python
# Debit amounts are summed
merged_entry['debit'] = entry1['debit'] + entry2['debit']

# Credit amounts are summed
merged_entry['credit'] = entry1['credit'] + entry2['credit']

# Currency amounts are summed
merged_entry['debit_in_account_currency'] += ...
merged_entry['credit_in_account_currency'] += ...
```

#### Example

**Input:**
```python
[
    {'account': 'Sales', 'debit': 500, 'cost_center': 'Main'},
    {'account': 'Sales', 'debit': 300, 'cost_center': 'Main'},
    {'account': 'Sales', 'debit': 200, 'cost_center': 'Main'}
]
```

**Output:**
```python
[
    {'account': 'Sales', 'debit': 1000, 'cost_center': 'Main'}
]
```

### _toggle_debit_credit_if_negative

Converts negative debits to credits and negative credits to debits.

#### Signature

```python
@staticmethod
def _toggle_debit_credit_if_negative(gl_map):
    """
    Toggle debit/credit for negative values.
    
    Args:
        gl_map (list): List of GL entry dictionaries
        
    Returns:
        list: GL map with negative values converted
    """
```

#### Conversion Rules

| Original | Converted |
|----------|-----------|
| Debit: -100, Credit: 0 | Debit: 0, Credit: 100 |
| Debit: 0, Credit: -100 | Debit: 100, Credit: 0 |
| Debit: 100, Credit: 0 | No change |
| Debit: 0, Credit: 100 | No change |

#### Example

```python
# Input
entry = {'debit': -50, 'credit': 0, 'debit_in_account_currency': -50}

# After processing
entry = {'debit': 0, 'credit': 50, 'debit_in_account_currency': 0, 
         'credit_in_account_currency': 50}
```

### Helper Methods

#### _get_cost_center_allocation_data

Fetches cost center allocation configuration from database.

```python
@staticmethod
@request_cache
def _get_cost_center_allocation_data(cost_center, company):
    """
    Get cost center allocation data.
    
    Args:
        cost_center (str): Parent cost center
        company (str): Company name
        
    Returns:
        list: Allocation data with percentages
    """
```

#### _get_merge_key

Generates a unique key for identifying mergeable entries.

```python
@staticmethod
def _get_merge_key(entry, accounting_dimensions):
    """
    Generate merge key for GL entry.
    
    Args:
        entry (dict): GL entry
        accounting_dimensions (list): List of dimension fields
        
    Returns:
        tuple: Unique key for merging
    """
```

## Data Structures

### GL Entry Dictionary

The standard structure for a GL entry:

```python
{
    # Required fields
    'account': str,              # Account name
    'debit': float,              # Debit amount
    'credit': float,             # Credit amount
    'voucher_type': str,         # Document type
    'voucher_no': str,           # Document number
    'posting_date': date,        # Transaction date
    
    # Optional fields
    'cost_center': str,          # Cost center
    'party_type': str,           # 'Customer', 'Supplier', etc.
    'party': str,                # Party name
    'against': str,              # Against account
    'against_voucher_type': str, # Reference doc type
    'against_voucher': str,      # Reference doc number
    'project': str,              # Project
    
    # Currency fields
    'account_currency': str,
    'debit_in_account_currency': float,
    'credit_in_account_currency': float,
    
    # Other fields
    'remarks': str,
    'is_opening': bool,
    'fiscal_year': str,
    'company': str
}
```

## Usage Examples

### Example 1: Basic Payment Entry

```python
from erpnext.accounts.services.general_ledger_service import GeneralLedgerService
from datetime import datetime

# Prepare GL entries for a payment
gl_entries = [
    {
        'account': 'Bank - ABC',
        'debit': 5000,
        'credit': 0,
        'party_type': 'Customer',
        'party': 'John Doe',
        'voucher_type': 'Payment Entry',
        'voucher_no': 'PE-2024-001',
        'posting_date': datetime(2024, 1, 15),
        'cost_center': 'Main - ABC'
    },
    {
        'account': 'Debtors - ABC',
        'debit': 0,
        'credit': 5000,
        'party_type': 'Customer',
        'party': 'John Doe',
        'voucher_type': 'Payment Entry',
        'voucher_no': 'PE-2024-001',
        'posting_date': datetime(2024, 1, 15),
        'cost_center': 'Main - ABC'
    }
]

# Process
result = GeneralLedgerService.process_gl_map(gl_entries)

print(f"Processed {len(result)} GL entries")
```

### Example 2: Sales Invoice with Multiple Line Items

```python
gl_entries = []

# Customer debit entry
gl_entries.append({
    'account': 'Debtors - ABC',
    'debit': 1180,  # Including tax
    'credit': 0,
    'party_type': 'Customer',
    'party': 'Customer A',
    'voucher_type': 'Sales Invoice',
    'voucher_no': 'SI-2024-001',
    'posting_date': datetime(2024, 1, 15),
    'cost_center': 'Sales - ABC'
})

# Sales credit entries (one per item)
for item in ['Item A', 'Item B', 'Item C']:
    gl_entries.append({
        'account': 'Sales - ABC',
        'debit': 0,
        'credit': 333.33,  # 1000 / 3 items
        'voucher_type': 'Sales Invoice',
        'voucher_no': 'SI-2024-001',
        'posting_date': datetime(2024, 1, 15),
        'cost_center': 'Sales - ABC'
    })

# Tax entry
gl_entries.append({
    'account': 'VAT - ABC',
    'debit': 0,
    'credit': 180,
    'voucher_type': 'Sales Invoice',
    'voucher_no': 'SI-2024-001',
    'posting_date': datetime(2024, 1, 15),
    'cost_center': 'Sales - ABC'
})

# Process - will merge 3 Sales entries into 1
result = GeneralLedgerService.process_gl_map(gl_entries, merge_entries=True)

print(f"Before: {len(gl_entries)} entries")
print(f"After: {len(result)} entries (Sales entries merged)")
```

### Example 3: Credit Note (Negative Values)

```python
# Credit note with negative amounts
gl_entries = [
    {
        'account': 'Debtors - ABC',
        'debit': -500,  # Negative debit
        'credit': 0,
        'party_type': 'Customer',
        'party': 'Customer A',
        'voucher_type': 'Sales Invoice',
        'voucher_no': 'SI-RTN-2024-001',
        'posting_date': datetime(2024, 1, 20),
        'cost_center': 'Sales - ABC'
    },
    {
        'account': 'Sales Returns - ABC',
        'debit': 0,
        'credit': -500,  # Negative credit
        'voucher_type': 'Sales Invoice',
        'voucher_no': 'SI-RTN-2024-001',
        'posting_date': datetime(2024, 1, 20),
        'cost_center': 'Sales - ABC'
    }
]

# Process - will convert negative values
result = GeneralLedgerService.process_gl_map(gl_entries)

# Result will have:
# Entry 1: Debit=0, Credit=500 (negative debit → positive credit)
# Entry 2: Debit=500, Credit=0 (negative credit → positive debit)
```

## Error Handling

### Empty GL Map

```python
gl_map = []
result = GeneralLedgerService.process_gl_map(gl_map)
# Returns: []
```

### None Values

The service handles None values gracefully:

```python
# Entry with None cost_center
entry = {
    'account': 'Cash',
    'debit': 100,
    'cost_center': None  # Will be handled correctly
}
```

### Missing Required Fields

While the service doesn't validate all required fields (that's done at the document level), it expects certain fields:

- `account`
- `debit` or `credit`
- `voucher_type`
- `voucher_no`

## Performance Considerations

### Request Caching

The `_get_cost_center_allocation_data` method uses `@request_cache` decorator to cache allocation data within a single request:

```python
@request_cache
def _get_cost_center_allocation_data(cost_center, company):
    # Database query cached for request duration
```

### Batch Processing

For large GL maps (100+ entries):

```python
# Process in batches if needed
batch_size = 100
for i in range(0, len(gl_map), batch_size):
    batch = gl_map[i:i+batch_size]
    processed = GeneralLedgerService.process_gl_map(batch)
    # Save processed batch
```

## Backward Compatibility

### Legacy Function Calls

The refactoring maintains backward compatibility. Old code continues to work:

```python
# OLD WAY (still works)
from erpnext.accounts.general_ledger import process_gl_map
result = process_gl_map(gl_entries)

# NEW WAY (recommended)
from erpnext.accounts.services.general_ledger_service import GeneralLedgerService
result = GeneralLedgerService.process_gl_map(gl_entries)
```

Both approaches produce identical results.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01 | Initial service layer extraction |

## See Also

- [General Ledger Overview](general_ledger_overview.md)
- [Service Layer Architecture](service_layer_architecture.md)
- [Testing Guide](testing_guide.md)

## Support

For issues or questions:
- Check test examples in `test_refactoring.py`
- Review service implementation in `accounts/services/general_ledger_service.py`
- Consult original Frappe/ERPNext documentation
