# Service Layer Architecture

## Overview

This document describes the service layer refactoring applied to ERPNext's accounts module, specifically focusing on the General Ledger processing logic.

## What is a Service Layer?

A service layer is an architectural pattern that:

- **Encapsulates business logic** in dedicated service classes
- **Provides a clear API** for application features
- **Sits between controllers and data access** layers
- **Enables testing** without full framework dependencies
- **Facilitates reuse** across different contexts

## Motivation for Refactoring

### Problems with Previous Architecture

Before refactoring, the `accounts/general_ledger.py` module had several issues:

1. **Tight Coupling**: Business logic mixed with database operations and framework calls
2. **Testing Difficulties**: Required full Frappe framework to test
3. **Low Maintainability**: Large functions with multiple responsibilities
4. **Poor Reusability**: Hard to use GL logic in different contexts
5. **Unclear Boundaries**: No clear separation between layers

### Example: Before Refactoring

```python
# general_ledger.py - Before
def process_gl_map(gl_map, merge_entries=True, precision=None, from_repost=False):
    """
    Mixed concerns: business logic + database calls + framework dependencies
    """
    # Business logic
    if gl_map[0].voucher_type != "Period Closing Voucher":
        # More business logic mixed with database queries
        for entry in gl_map:
            allocation_data = frappe.db.get_value(...)  # Database call
            # Process allocation
    
    # More mixed logic
    if merge_entries:
        # Merging logic
    
    return gl_map
```

**Issues:**
- ❌ Can't test without database
- ❌ Business logic not isolated
- ❌ Hard to understand flow
- ❌ Difficult to mock dependencies

## The Service Layer Solution

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Presentation Layer                 │
│              (UI, API Controllers, Doctypes)         │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│                    Service Layer                     │
│        (GeneralLedgerService, OrderService, etc.)    │
│  • Pure business logic                               │
│  • No framework dependencies                         │
│  • Testable in isolation                             │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│                 Data Access Layer                    │
│              (frappe.db, Document API)               │
└─────────────────────────────────────────────────────┘
```

### New Structure

```
accounts/
├── general_ledger.py          # Thin wrapper, delegates to service
├── services/                   # NEW: Service layer
│   ├── __init__.py
│   └── general_ledger_service.py  # Pure business logic
└── ...
```

### Example: After Refactoring

```python
# accounts/services/general_ledger_service.py
class GeneralLedgerService:
    """
    Pure business logic - no framework dependencies in core methods
    """
    
    @staticmethod
    def process_gl_map(gl_map, merge_entries=True, precision=None, from_repost=False):
        """
        Orchestrates GL processing steps
        """
        if not gl_map:
            return []
        
        # Clear business logic flow
        if gl_map[0].voucher_type != "Period Closing Voucher":
            gl_map = GeneralLedgerService._distribute_gl_based_on_cost_center_allocation(
                gl_map, precision, from_repost
            )
        
        if merge_entries:
            gl_map = GeneralLedgerService._merge_similar_entries(gl_map, precision)
        
        gl_map = GeneralLedgerService._toggle_debit_credit_if_negative(gl_map)
        
        return gl_map
```

```python
# accounts/general_ledger.py
from erpnext.accounts.services.general_ledger_service import GeneralLedgerService

def process_gl_map(gl_map, merge_entries=True, precision=None, from_repost=False):
    """
    Thin wrapper that delegates to service
    Maintains backward compatibility
    """
    return GeneralLedgerService.process_gl_map(gl_map, merge_entries, precision, from_repost)
```

**Benefits:**
- ✅ Business logic isolated in service class
- ✅ Can test with simple mocks
- ✅ Clear, understandable structure
- ✅ Easy to reuse in different contexts
- ✅ Backward compatible

## Key Architectural Principles

### 1. Separation of Concerns

Each layer has a distinct responsibility:

- **Controllers/Doctypes**: Handle HTTP requests, validation, orchestration
- **Service Layer**: Implements business rules and domain logic
- **Data Access**: Manages database operations and queries

### 2. Dependency Inversion

```python
# High-level modules should not depend on low-level modules
# Both should depend on abstractions

# ✅ Good: Service depends on abstraction
class GeneralLedgerService:
    def process(self, data):
        # Pure business logic
        return processed_data

# ❌ Bad: Service depends on concrete framework
class GeneralLedgerService:
    def process(self, data):
        result = frappe.db.get_value(...)  # Tight coupling
        return result
```

### 3. Single Responsibility Principle

Each method does ONE thing:

```python
class GeneralLedgerService:
    # ✅ Each method has single, clear purpose
    
    @staticmethod
    def process_gl_map():
        """Orchestrates the entire GL processing flow"""
        pass
    
    @staticmethod
    def _distribute_gl_based_on_cost_center_allocation():
        """Handles ONLY cost center distribution"""
        pass
    
    @staticmethod
    def _merge_similar_entries():
        """Handles ONLY entry merging"""
        pass
```

## Seven Key Advantages

### 1. Improved Maintainability

**Before:**
- 450+ lines in single file
- Mixed concerns
- Hard to navigate

**After:**
- Clear separation
- Small, focused methods
- Easy to locate logic

### 2. Reduced Coupling

**Before:**
```python
# Tight coupling to Frappe framework
frappe.db.get_value(...)
frappe.get_doc(...)
frappe.throw(...)
```

**After:**
```python
# Service layer isolates business logic
# Framework calls delegated to wrapper
```

### 3. Enhanced Testability

**Before:**
- Required full Frappe setup
- Database needed for tests
- Slow test execution

**After:**
```python
# Can test with simple mocks
def test_merge_entries():
    gl_map = [
        {"account": "Sales", "debit": 500},
        {"account": "Sales", "debit": 500}
    ]
    result = GeneralLedgerService._merge_similar_entries(gl_map)
    assert len(result) == 1
    assert result[0]["debit"] == 1000
```

### 4. Scalability Preparation

Service layer makes it easier to:
- Extract services into microservices
- Scale independently
- Deploy separately
- Use different databases

### 5. Clear API Boundaries

```python
# Public API (External interface)
GeneralLedgerService.process_gl_map()

# Private methods (Internal implementation)
GeneralLedgerService._distribute_gl_based_on_cost_center_allocation()
GeneralLedgerService._merge_similar_entries()
GeneralLedgerService._toggle_debit_credit_if_negative()
```

### 6. Easier Debugging

- Business logic isolated
- Can trace flow easily
- Single responsibility per method
- Clear call hierarchy

### 7. Better Documentation

```python
class GeneralLedgerService:
    """
    Service class for General Ledger operations.
    
    This class provides a service layer for processing GL entries,
    helping to decouple business logic from direct database operations
    and improving testability and maintainability.
    """
```

## Implementation Details

### Static Methods vs Instance Methods

Currently using **static methods** because:
- No state is maintained
- Pure functions (input → output)
- Easy to call without instantiation
- Suitable for utility/business logic

Future evolution could use instance methods if state is needed.

### Backward Compatibility Strategy

The refactoring maintains 100% backward compatibility:

```python
# Old code continues to work
from erpnext.accounts.general_ledger import process_gl_map
result = process_gl_map(gl_entries)

# Wrapper function delegates to service
def process_gl_map(gl_map, merge_entries=True, precision=None, from_repost=False):
    return GeneralLedgerService.process_gl_map(gl_map, merge_entries, precision, from_repost)
```

**No breaking changes:**
- ✅ Same function signatures
- ✅ Same return values
- ✅ Same behavior
- ✅ All existing code works

## Testing Strategy

### Unit Tests

Test business logic in isolation:

```python
def test_basic_gl_processing():
    """Test basic GL map processing"""
    gl_map = create_test_data()
    result = GeneralLedgerService.process_gl_map(gl_map)
    assert len(result) == 2
```

### Integration Tests

Test with real framework:

```python
def test_with_frappe():
    """Test with actual Frappe framework"""
    # Create real document
    doc = frappe.get_doc({...})
    doc.submit()
    # Verify GL entries created
```

## Future Enhancements

### Phase 2: More Service Classes

Extract additional services:

```
accounts/services/
├── general_ledger_service.py     ✅ Done
├── payment_service.py             🔄 Planned
├── invoice_service.py             🔄 Planned
├── reconciliation_service.py      🔄 Planned
└── reporting_service.py           🔄 Planned
```

### Phase 3: Microservices Architecture

```
┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│  API Gateway │
└──────────────┘     └──────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │     GL      │  │   Payment   │  │   Invoice   │
   │   Service   │  │   Service   │  │   Service   │
   └─────────────┘  └─────────────┘  └─────────────┘
```

### Phase 4: Event-Driven Architecture

```python
# Publish events
event_bus.publish("gl_entry.created", data)

# Subscribe to events
@subscribe("gl_entry.created")
def update_trial_balance(event_data):
    # Update reporting tables
    pass
```

## Best Practices

### DO ✅

1. Keep business logic in service layer
2. Use dependency injection for external dependencies
3. Write unit tests for all service methods
4. Document public APIs clearly
5. Maintain backward compatibility
6. Follow single responsibility principle

### DON'T ❌

1. Don't put database queries in service methods
2. Don't mix presentation logic with business logic
3. Don't create god classes (too many responsibilities)
4. Don't break existing APIs without migration path
5. Don't skip documentation
6. Don't forget to write tests

## Conclusion

The service layer refactoring improves the ERPNext accounts module by:

- ✅ Separating concerns clearly
- ✅ Making code more testable
- ✅ Improving maintainability
- ✅ Preparing for future scalability
- ✅ Maintaining backward compatibility

This is the foundation for further architectural improvements and eventual microservices migration.

## References

- [General Ledger Overview](general_ledger_overview.md)
- [Testing Guide](testing_guide.md)
- [API Reference](api_reference.md)
