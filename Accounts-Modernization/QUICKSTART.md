# ⚡ QUICKSTART - Run This Feature in 5 Minutes

## Prerequisites ✅

- Python 3.8+ installed
- pip installed

## Step-by-Step Instructions 🚀

### 1️⃣ Install Dependencies (if not already done)

```powershell
# Navigate to project root
cd D:\Internships\PearlThoughts-Internship\Erpnext-Refactoring

# Install required packages
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

```powershell
# Create .env file from template (if not exists)
copy .env.template .env

# Edit .env and add your Groq API key
notepad .env
```

**Add this line to .env:**
```
GROQ_API_KEY=your_api_key_here
```

> 💡 Get free API key from: https://console.groq.com

### 3️⃣ Verify Setup

```powershell
# Navigate to Accounts-Modernization folder
cd Accounts-Modernization

# Run setup verification
python verify_setup.py
```

**Expected output:**
```
✓ Python Version
✓ Dependencies
✓ Go Installation (or warning - optional)
✓ Environment Config
✓ Directory Structure
✓ Accounts Module
```

### 4️⃣ Run Quick Example

```powershell
# Run the example script
python example.py
```

This will:
- ✅ Scan a Python file
- ✅ Analyze dependencies using AST
- ✅ Show classes and functions found
- ✅ Generate logs

### 5️⃣ Run Full Conversion

```powershell
# Convert a single file
python cli/main.py convert ../accounts/party.py

# OR convert entire accounts folder
python cli/main.py convert ../accounts/
```

**What happens:**
1. 📋 Scans Python files
2. 🔍 Analyzes dependencies (AST)
3. 📝 Prepares context
4. 🤖 Converts Python → Go (AI)
5. ✅ Generates Go code in `modern/`

### 6️⃣ Run Tests

```powershell
# Test Go code compilation
python tests/unit/test_go_code.py

# Test module integration
python tests/integration/test_module_integration.py

# Test accounting scenarios
python tests/functional/test_accounting_scenarios.py

# Run QA validation
python tests/qa_validation/qa_validator.py

# OR run all tests
pytest tests/
```

### 7️⃣ Review Output

```powershell
# View generated Go code
dir modern

# View conversion report
type results\conversion_report_*.txt

# View scan log
type logs\scan_*.log
```

---

## 🎯 Common Use Cases

### Use Case 1: Convert Single File

```powershell
cd D:\Internships\PearlThoughts-Internship\Erpnext-Refactoring\Accounts-Modernization

python cli/main.py convert ../accounts/party.py
python tests/unit/test_go_code.py
```

### Use Case 2: Convert Entire Module

```powershell
cd D:\Internships\PearlThoughts-Internship\Erpnext-Refactoring\Accounts-Modernization

python cli/main.py convert ../accounts/
python tests/qa_validation/qa_validator.py
```

### Use Case 3: Full Workflow with Testing

```powershell
cd D:\Internships\PearlThoughts-Internship\Erpnext-Refactoring\Accounts-Modernization

# Convert
python cli/main.py convert ../accounts/general_ledger.py

# Test
python tests/unit/test_go_code.py
python tests/integration/test_module_integration.py
python tests/functional/test_accounting_scenarios.py

# Validate
python tests/qa_validation/qa_validator.py

# Review
type results\qa_report_*.txt
```

---

## 📁 Output Locations

After running conversion:

- **Go Code**: `modern/` folder
  - `modern/invoice/` → Invoice-related Go code
  - `modern/ledger/` → Ledger-related Go code
  - `modern/tax/` → Tax-related Go code

- **Logs**: `logs/` folder
  - `scan_*.log` → File scanning results
  - `dependency_*.log` → Dependency analysis
  - `cli.log` → CLI execution log

- **Results**: `results/` folder
  - `conversion_report_*.txt` → Conversion summary
  - `qa_report_*.txt` → QA validation report
  - `functional_tests.jsonl` → Test results

---

## 🆘 Troubleshooting

### Error: "Module not found"

```powershell
# Install missing packages
pip install python-dotenv groq pytest astroid
```

### Error: "GROQ_API_KEY not set"

```powershell
# Edit .env file
notepad .env

# Add: GROQ_API_KEY=your_key_here
```

### Error: "Path not found"

```powershell
# Use absolute path
python cli/main.py convert "D:\Internships\PearlThoughts-Internship\Erpnext-Refactoring\accounts"
```

### Error: "Go compiler not found" (when testing)

This is optional. Go is only needed for testing compiled Go code.

**Option 1:** Install Go from https://go.dev/dl/

**Option 2:** Skip Go compilation tests (other tests will still work)

---

## 🎓 What Each Command Does

| Command | Purpose |
|---------|---------|
| `python verify_setup.py` | Checks that everything is configured correctly |
| `python example.py` | Runs a simple demonstration |
| `python cli/main.py convert <path>` | Converts Python to Go |
| `python tests/unit/test_go_code.py` | Tests Go code compilation |
| `python tests/integration/test_module_integration.py` | Tests module interactions |
| `python tests/functional/test_accounting_scenarios.py` | Tests business logic |
| `python tests/qa_validation/qa_validator.py` | Comprehensive QA check |
| `pytest tests/` | Runs all tests |

---

## ✅ Success Checklist

After running the commands, verify:

- [ ] `verify_setup.py` passes all checks
- [ ] `example.py` runs without errors
- [ ] `cli/main.py convert` generates Go code in `modern/`
- [ ] Logs are created in `logs/`
- [ ] Conversion report exists in `results/`
- [ ] At least one test passes

---

## 📚 Next Steps

1. ✅ Run through this quickstart
2. 📖 Read [GETTING_STARTED.md](GETTING_STARTED.md) for detailed guide
3. 📖 Read [README.md](README.md) for project overview
4. 🧪 Experiment with different files
5. 🔍 Review generated Go code
6. 🎯 Customize for your needs

---

## 🚀 You're Ready!

That's it! You now have a working CLI system that:
- ✅ Scans Python Accounts code
- ✅ Analyzes dependencies using AST
- ✅ Converts to Go using AI
- ✅ Validates with comprehensive tests
- ✅ Produces detailed reports

**Start converting:**
```powershell
python cli/main.py convert ../accounts/
```

🎉 Happy Converting!
