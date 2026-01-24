# Accounts-Modernization

CLI-based system to convert ERPNext Accounts module from Python to Go.

## Overview

Accounts-Modernization is a comprehensive conversion system that:
- Analyzes Python code using AST
- Converts to Go using AI (Groq)
- Validates through comprehensive testing
- Ensures accounting business logic preservation

## Project Structure

```
Accounts-Modernization/
├── cli/                    # CLI entry point
│   ├── __init__.py
│   └── main.py            # accounts-modernizor command
├── backend/               # Python analysis & conversion logic
│   ├── analyzer/          # AST-based code analyzer
│   │   ├── scanner.py
│   │   └── dependency_analyzer.py
│   ├── converter/         # AI-powered converter
│   │   └── ai_converter.py
│   └── utils/             # Configuration & logging
│       ├── config.py
│       └── logger.py
├── modern/                # Generated Go code
│   ├── invoice/
│   ├── ledger/
│   ├── tax/
│   └── ...
├── tests/                 # Testing & QA
│   ├── unit/              # Go code unit tests
│   ├── integration/       # Module integration tests
│   ├── functional/        # Accounting scenario tests
│   └── qa_validation/     # QA validation scripts
├── logs/                  # Runtime logs
└── results/              # Conversion & test results
```

## Installation

1. Install Python dependencies:
```bash
pip install -r ../requirements.txt
```

2. Set up environment variables:
```bash
# Copy template
copy ..\.env.template ..\.env

# Edit .env and add your GROQ_API_KEY
```

3. Install Go (for testing compiled Go code):
```
https://go.dev/dl/
```

## Usage

### Convert Accounts Module

```bash
# Convert single file
python cli/main.py convert ../accounts/party.py

# Convert entire accounts folder
python cli/main.py convert ../accounts/

# Convert with absolute path
python cli/main.py convert "D:\path\to\accounts\"
```

### Run Tests

```bash
# Unit tests (Go code validation)
python tests/unit/test_go_code.py

# Integration tests
python tests/integration/test_module_integration.py

# Functional tests (accounting scenarios)
python tests/functional/test_accounting_scenarios.py

# QA validation
python tests/qa_validation/qa_validator.py

# Or use pytest
pytest tests/
```

## Conversion Workflow

1. **Scan**: Identifies Python files and validates syntax
2. **Analyze**: Extracts dependencies, imports, classes, functions using AST
3. **Prepare Context**: Summarizes business logic and relationships
4. **Convert**: AI converts Python to Go, preserving accounting logic
5. **Test**: Validates through unit, integration, and functional tests
6. **QA**: Comprehensive quality assurance validation

## Output Files

- **modern/**: Generated Go code organized by module
- **logs/**: Detailed logs for scan, dependency analysis, and conversion
- **results/**: Conversion reports and test results

## Key Features

- ✅ CLI-first design
- ✅ AST-based static analysis
- ✅ AI-powered conversion (Groq)
- ✅ Template fallback (when AI unavailable)
- ✅ Comprehensive testing (unit/integration/functional/QA)
- ✅ Accounting business logic preservation
- ✅ Detailed logging and reporting

## Requirements

- Python 3.8+
- Groq API key (for AI conversion)
- Go 1.19+ (for testing compiled Go code)

## Notes

- This is a CLI-only, backend-only system
- Focus on correctness and accounting integrity
- Manual review can be minimized/eliminated through automated validation (see below)

## Minimizing Manual Review

The system provides automated validation to reduce or eliminate manual code review:

### Automated Quality Checks
1. **Syntax Validation** - Go code syntax automatically verified
2. **Compilation Tests** - All Go files compiled and checked for errors
3. **Business Logic Tests** - Accounting rules validated automatically
4. **Integration Tests** - Module interactions tested
5. **QA Validation** - Comprehensive quality assurance checks

### Confidence Score System
The system calculates a confidence score (0-100%) based on:
- ✅ Syntax validation (10%)
- ✅ Compilation success (15%)
- ✅ Unit tests pass rate (25%)
- ✅ Integration tests (20%)
- ✅ Business logic validation (20%)
- ✅ Code quality metrics (10%)

**95%+ Confidence Score = Production Ready (No manual review needed)**

### Steps to Achieve Zero Manual Review
1. Run full conversion: `python cli/main.py convert ../accounts/`
2. Execute all tests: `pytest tests/`
3. Run QA validation: `python tests/qa_validation/qa_validator.py`
4. Check confidence score in QA report
5. If score ≥95%, code is production-ready

**For detailed architecture and validation workflow, see [ARCHITECTURE.md](ARCHITECTURE.md)**
