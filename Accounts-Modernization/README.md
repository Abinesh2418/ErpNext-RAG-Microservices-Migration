# Accounts-Modernization

**CLI-based Python → Go conversion system powered by Groq API with Redis caching and Qdrant semantic search**

Automates the conversion of ERPNext Accounts module from Python to Go with intelligent caching, semantic context, and comprehensive validation.

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Project Description](#-project-description)
- [Architecture Principles](#-architecture-principles)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#-usage)
- [Testing](#-testing)
- [How It Works](#-how-it-works)
- [Technology Stack](#-technology-stack)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)
- [Contact](#-contact)

---

## 🎯 Project Overview

Accounts-Modernization is a production-ready, CLI-based conversion system that automates the transformation of ERPNext's Python-based Accounts module into idiomatic, production-ready Go code. The system leverages Groq's powerful LLM API (llama-3.3-70b-versatile) for intelligent code conversion while maintaining business logic integrity through comprehensive validation.

**Key Capabilities:**

✅ **Intelligent Analysis** - Python AST-based static code analysis  
✅ **Smart Caching** - Redis-based caching for instant re-conversion (600x faster)  
✅ **Semantic Context** - Qdrant vector database for meaning-based context retrieval  
✅ **AI-Powered Conversion** - Groq API with llama-3.3-70b-versatile model  
✅ **Comprehensive Validation** - Automated Go syntax and compilation checks  
✅ **Business Logic Preservation** - Zero data integrity loss with accounting rules intact  

---

## 📋 Project Description

### The Challenge

Converting a complex accounting ERP system from Python to Go while:
- Preserving intricate business logic (invoice management, ledger entries, tax calculations)
- Maintaining data integrity and accounting rules
- Ensuring production-ready code quality
- Minimizing manual intervention and review time

### The Solution

A sophisticated 5-phase conversion pipeline:

1. **Static Analysis** - AST-based code understanding without execution
2. **Smart Caching** - SHA-256 hash-based change detection with Redis
3. **Semantic Indexing** - Ollama-powered embeddings stored in Qdrant (768-dimensional vectors)
4. **AI Conversion** - Groq API (llama-3.3-70b-versatile) with context-aware prompts
5. **Automated Validation** - Go compiler checks and syntax validation

### Key Features

- **🚀 Speed**: First run ~54s/file, cached runs ~0.05s/file (600x improvement)
- **🎯 Quality**: High-parameter model (70B) for superior code generation
- **🔄 Incremental**: Only converts changed files, preserves cache for others
- **🧠 Context-Aware**: Semantic search provides relevant code examples to AI
- **✅ Validated**: Every conversion is syntax-checked and compilation-tested
- **📊 Transparent**: Complete audit trail with detailed logs and reports

---

## 🏗️ Architecture Principles

| Component | Role | Purpose |
|-----------|------|---------|
| **Python AST** | Truth Provider | Provides structural facts without code execution |
| **Redis** | Structure & Speed | Caches hashes, AST, dependencies, conversions |
| **Qdrant** | Semantic Memory | Stores code meanings for context retrieval |
| **Ollama** | Embedding Generator | Local embeddings (nomic-embed-text:v1.5, 768-dim) |
| **Groq API** | AI Translator | Converts code using llama-3.3-70b-versatile |
| **Go Compiler** | Quality Gate | Validates generated code |

**Conversion Flow**: AST analyzes → Redis caches → Qdrant provides context → Groq converts → Go validates

---

## 📁 Project Structure

```
Accounts-Modernization/
├── cli/                           # CLI entry point
│   ├── __init__.py
│   └── main.py                   # Main CLI command
│
├── backend/                      # Core conversion logic
│   ├── analyzer/                 # Static analysis & caching
│   │   ├── scanner.py            # File discovery & syntax check
│   │   ├── dependency_analyzer.py # AST-based dependency extraction
│   │   ├── redis_store.py        # 🆕 Redis cache layer
│   │   └── qdrant_index.py       # 🆕 Semantic index
│   │
│   ├── converter/                # Python → Go conversion
│   │   └── ai_converter.py       # AI conversion with caching
│   │
│   └── utils/                    # Configuration & logging
│       ├── config.py
│       └── logger.py
│
├── modern/                       # 📦 Generated Go code
│   ├── invoice/                  # Go invoice module
│   ├── ledger/                   # Go ledger module
│   ├── tax/                      # Go tax module
│   ├── party/                    # Go party module
│   └── ...
│
├── tests/                        # 🧪 Multi-level testing
│   ├── unit/                     # Go compilation & syntax tests
│   ├── integration/              # Module integration tests
│   ├── functional/               # Accounting scenario tests
│   └── qa_validation/            # Automated QA validation
│
├── logs/                         # 📋 Runtime logs
│   ├── scan_*.log
│   ├── dependency_*.log
│   └── conversion_*.log
│
├── results/                      # 📊 Reports & metrics
│   ├── conversion_report_*.txt
│   └── qa_report_*.txt
│
├── ARCHITECTURE.md               # Detailed system architecture
├── ARCHITECTURE_REDIS_QDRANT_SECTIONS.md  # New sections on caching
├── SYSTEM_DESIGN.md              # System design document
└── README.md                     # This file
```

---

## 🚀 Getting Started

### Prerequisites

1. **Python 3.8+** - Core runtime
2. **Groq API Key** - For AI conversion ([Get key](https://console.groq.com))
3. **Ollama** - For local embeddings generation
4. **Redis 5.0+** - For caching
5. **Qdrant 1.7.0+** - For semantic search
6. **Go 1.19+** - For validating generated code

### Installation

#### 1. Install Python Dependencies

```bash
cd d:\Internships\PearlThoughts-Internship\Erpnext-Refactoring
pip install -r requirements.txt
```

This installs:
- `python-dotenv` - Environment variable management
- `redis` - Redis client for caching
- `qdrant-client` - Qdrant vector database client
- `requests` - HTTP client for Groq API
- `astroid` - Advanced AST analysis

#### 2. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com)
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `gsk_...`)

#### 3. Install and Start Ollama (for embeddings)

**Windows:**
```bash
# Download from https://ollama.ai/download
# Install and run Ollama

# Pull embedding model only
ollama pull nomic-embed-text:v1.5
```

**Linux/Mac:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull embedding model
ollama pull nomic-embed-text:v1.5

# Start Ollama service
ollama serve
```

#### 4. Start Redis

**Windows:**
```bash
# Download from https://redis.io/download
# Or use Docker:
docker run -d -p 6379:6379 redis:latest
```

**Linux/Mac:**
```bash
sudo service redis-server start
# Or: redis-server
```

#### 5. Start Qdrant

**Docker (Recommended):**
```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

**Or download from:** https://qdrant.tech/documentation/quick-start/

#### 6. Configure Environment

Create a `.env` file in the **root directory** (Erpnext-Refactoring/):

```bash
# Groq API Configuration (for AI conversion)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Ollama Configuration (for embeddings only)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text:v1.5

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Conversion Settings
AI_TEMPERATURE=0.2
PRIMARY_WORKERS=4
MAX_FILE_SIZE_MB=10
ENABLE_SYNTAX_CHECK=true
```

**⚠️ Important**: The `.env` file must be in the **root directory** (Erpnext-Refactoring/), not in Accounts-Modernization/

---

## 💻 Usage

### Convert Python Files to Go

#### Single File
```bash
cd Accounts-Modernization
python cli/main.py convert ../accounts/party.py
```

#### Entire Folder
```bash
python cli/main.py convert ../accounts/
```

#### With Absolute Path
```bash
python cli/main.py convert "D:\path\to\accounts\"
```

### What Happens During Conversion?

```
1. 📂 SCAN: Discover Python files
   └─► Validate syntax using Python AST
   └─► Extract file metadata (size, lines, etc.)
       
2. 🔍 ANALYZE: AST-based code understanding
   └─► Extract imports, classes, functions
   └─► Build dependency graph
   └─► Check Redis for cached AST
       └─► If found: Reuse cached analysis
       └─► If new: Analyze and cache in Redis
   
3. 🕸️ INDEX: Semantic meaning storage
   └─► Generate embeddings using Ollama (768-dim vectors)
   └─► Store file & function meanings in Qdrant
   └─► Enable context-aware conversion
   
4. 🤖 CONVERT: AI-powered Python → Go
   └─► Check Redis cache (SHA-256 hash)
       └─► If file unchanged: Use cached Go code (0.05s)
       └─► If changed: Proceed with conversion
   └─► Fetch relevant context from Qdrant (top-3 matches)
   └─► Build enhanced prompt with business rules
   └─► Call Groq API (llama-3.3-70b-versatile)
   └─► Stream response with early stop detection
   └─► Extract and clean Go code
   └─► Cache result in Redis for future runs
   
5. ✅ VALIDATE: Quality checks
   └─► Go syntax validation (gofmt)
   └─► Compilation test (go build)
   └─► Generate conversion report
   
6. 💾 SAVE: Write Go files
   └─► Organize into modules (party/, invoice/, ledger/, etc.)
   └─► Save to modern/ directory
```

### Performance

**First Conversion (No Cache):**
- Small file (100 lines): ~15-20 seconds
- Medium file (500 lines): ~30-40 seconds  
- Large file (1000+ lines): ~50-60 seconds

**Cached Conversion (File Unchanged):**
- Any size: ~0.05 seconds (⚡ **600x faster**)

**Typical 50-File Project:**
- First run: ~40-45 minutes
- Second run (2 files changed): ~3-5 minutes (🚀 **15x faster**)

### View Conversion Results

```bash
# Check generated Go code
ls modern/

# View conversion report
cat results/conversion_report_TIMESTAMP.txt

# Check logs
cat logs/conversion_TIMESTAMP.log
```

---

## 🧪 Testing

### Validate Conversion with go_test.py

```bash
cd Accounts-Modernization

# Test Groq API connection
python go_test.py api

# Validate Go syntax
python go_test.py syntax

# Test Go compilation
python go_test.py compile

# Test conversion pipeline on a file
python go_test.py convert ../accounts/party.py

# Analyze conversion results
python go_test.py results

# Run all tests
python go_test.py all
```

### Test Coverage

- **API Connection**: Validates Groq API connectivity and authentication
- **Syntax Validation**: Checks all generated Go files for syntax errors (gofmt)
- **Compilation**: Verifies Go code compiles successfully (go build)
- **Conversion Pipeline**: End-to-end testing of Python→Go conversion
- **Results Analysis**: Reviews conversion reports and metrics

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------||
| **Language** | Python 3.8+ | Analysis & orchestration |
| **AST Parser** | Python `ast` / `astroid` | Static code analysis |
| **Cache** | Redis 5.0+ | Structure, dependencies & conversion cache |
| **Vector DB** | Qdrant 1.7.0+ | Semantic search (768-dimensional) |
| **Embeddings** | Ollama (nomic-embed-text:v1.5) | Local vector generation |
| **AI Conversion** | Groq API (llama-3.3-70b-versatile) | Python → Go conversion |
| **Target Language** | Go 1.19+ | Output language |
| **Validation** | Go compiler (gofmt, go build) | Code quality assurance |
| **Environment** | python-dotenv | Configuration management |

### Key Technologies

**Groq API:**
- Model: llama-3.3-70b-versatile (70B parameters)
- Context window: 131,072 tokens
- Temperature: 0.2 (deterministic output)
- Streaming API support for faster response
- High-performance inference

**Redis:**
- File hash storage (SHA-256)
- AST results caching
- Dependency graph storage
- Conversion output caching

**Qdrant:**
- 768-dimensional vector storage
- Semantic similarity search
- File and function meaning indexing
- Fast context retrieval for AI prompts

**Ollama:**
- Local embedding generation
- Model: nomic-embed-text:v1.5
- Fast, privacy-preserving vector creation

---

## 🎓 How It Works

### Complete 5-Phase Conversion Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│  PHASE 1: SCAN & VALIDATE (2-5 seconds)                       │
│  • Discover .py files recursively                              │
│  • Validate Python syntax using AST                            │
│  • Extract metadata (size, lines, etc.)                        │
└──────────────┬─────────────────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────────┐
│  PHASE 2: AST ANALYSIS (5-10 seconds/file)                    │
│  • Parse Python AST (Abstract Syntax Tree)                     │
│  • Extract imports, classes, functions                         │
│  • Build dependency graph                                      │
│  • Cache results in Redis (for next run)                      │
└──────────────┬─────────────────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────────┐
│  PHASE 3: SEMANTIC INDEXING (1-2 min, one-time)               │
│  • Generate embeddings using Ollama (768-dim)                  │
│  • Store file meanings in Qdrant                               │
│  • Store function meanings in Qdrant                           │
│  • Enable semantic context retrieval                           │
└──────────────┬─────────────────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────────┐
│  PHASE 4: AI CONVERSION (10-30s OR 0.05s cached)               │
│  • Check Redis cache (SHA-256 hash)                            │
│      └─ Unchanged? Return cached Go code (0.05s)              │
│  • Query Qdrant for relevant context (top-3)                   │
│  • Build enhanced prompt with business rules                   │
│  • Call Groq API (llama-3.3-70b-versatile)                    │
│  • Stream response with early stop detection                   │
│  • Extract & validate Go code                                  │
│  • Cache result in Redis                                       │
└──────────────┬─────────────────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────────┐
│  PHASE 5: VALIDATE & SAVE (5-10 seconds)                      │
│  • Validate Go syntax (gofmt)                                  │
│  • Test compilation (go build)                                 │
│  • Organize into modules (party/, invoice/, etc.)             │
│  • Write to modern/ directory                                  │
│  • Generate conversion report                                  │
└────────────────────────────────────────────────────────────────┘
```

### Incremental Conversion with Caching

For each Python file, the system:

```python
# 1. Compute file hash
file_hash = SHA256(file_content)

# 2. Check Redis cache
if redis.get(f"conversion:{file_path}") and redis.get(f"hash:{file_path}") == file_hash:
    # File unchanged - use cached Go code
    go_code = redis.get(f"conversion:{file_path}")
    return go_code  # ⚡ 0.05 seconds!

# 3. File changed or new - convert
go_code = convert_with_groq_api(file_content, context)

# 4. Cache for future
redis.set(f"conversion:{file_path}", go_code)
redis.set(f"hash:{file_path}", file_hash)
```

### Context-Aware Conversion

```python
# For file: party.py

# 1. Query Qdrant for semantic context
context = qdrant.search(
    query="party management customer supplier accounting",
    top_k=3
)
# Returns:
# - File party.py: Party management (score: 0.89)
# - Function get_party_balance: Calculate outstanding (score: 0.76) 
# - Links to general_ledger.py (score: 0.68)

# 2. Build enhanced prompt
prompt = f"""
Convert this Python code to Go.

RELEVANT CONTEXT:
{context}

PYTHON CODE:
{python_code}

REQUIREMENTS:
- Preserve business logic
- Use idiomatic Go patterns
- Add error handling
"""

# 3. Call Groq API
response = groq.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2,
    stream=True
)
```

### Benefits

✅ **600x Faster**: Cached conversions (0.05s vs 30s)  
✅ **Context-Aware**: Relevant code examples automatically included  
✅ **Incremental**: Only converts changed files  
✅ **Quality**: 70B parameter model for superior output  
✅ **Validated**: Every conversion tested for syntax and compilation

---

## 🚧 Troubleshooting

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# If not running, start Redis:
# Windows: redis-server.exe
# Linux: sudo service redis-server start
```

### Qdrant Connection Failed
```bash
# Check Qdrant is running
curl http://localhost:6333

# If not running:
docker run -d -p 6333:6333 qdrant/qdrant
```

### Ollama Not Responding (For Embeddings)
```bash
# Check Ollama is running
curl http://localhost:11434

# Start Ollama service:
# Windows: Ollama should auto-start
# Linux/Mac: ollama serve

# Verify embedding model is installed:
ollama list

# Pull embedding model if missing:
ollama pull nomic-embed-text:v1.5
```

### Groq API Issues
```bash
# Check API key is set in .env file (root directory)
grep GROQ_API_KEY ../. env

# Test API connection:
python go_test.py api

# Verify model availability:
# Visit: https://console.groq.com/
```

---

## � Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture and design
- **[CONVERSION_FLOW.md](CONVERSION_FLOW.md)** - Detailed conversion flow walkthrough with code references
---

## 🙏 Acknowledgments

- **ERPNext** - Source accounting system providing the Python codebase
- **Groq** - High-performance LLM API infrastructure
- **Meta AI** - LLaMA 3.3 foundation model (70B parameters)
- **Ollama** - Local embedding generation runtime
- **Redis Labs** - High-performance in-memory caching
- **Qdrant** - Vector similarity search engine
- **Go Team** - Target language and compiler

---

## 📬 Contact

For queries or suggestions:

- 📧 **Email**: abineshbalasubramaniyam@example.com  
- 💼 **LinkedIn**: [Abinesh B](https://linkedin.com/in/abinesh-b-1b14a1290/)  
- 🐙 **GitHub**: [Abinesh2418](https://github.com/Abinesh2418)

---
