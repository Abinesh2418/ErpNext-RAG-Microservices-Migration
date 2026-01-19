# ERPNext Accounts Module - Refactoring

## 🎯 Project Overview

This project demonstrates **comprehensive refactoring and modernization of the ERPNext accounts module** through four major features:

1. **Service Layer Architecture** - Extracted business logic into dedicated service classes
2. **AI-Powered RAG System** - Intelligent code documentation using LanceDB + Groq
3. **Microservices Architecture** - Event-driven design with invoice, ledger, and tax services
4. **VS Code Extension** - IDE-integrated RAG assistant for seamless code querying

The goal is to improve code organization, maintainability, and prepare the codebase for future modernization while making it instantly queryable through natural language AI.

**Key Highlights**: 
- ✅ **NO behavior changes** - All functionality works exactly as before!
- 🤖 **AI-Powered Documentation** - Query codebase using natural language with RAG system
- 🔌 **VS Code Integration** - RAG assistant directly in your IDE
- 🚀 **Microservices Ready** - Event-driven architecture demonstration

---

## 📝 Project Description

### What Was Done

#### **Feature 1: Service Layer Refactoring**
- Created `accounts/services/` folder structure
- Implemented `GeneralLedgerService` class
- Extracted GL processing business logic from monolithic code
- Maintained 100% backward compatibility
- Created automated test suite with 4 comprehensive test cases

#### **Feature 2: AI-Powered RAG System**
- Implemented Retrieval-Augmented Generation using LanceDB + Groq
- Created 4 comprehensive documentation files (1,650+ lines)
- Automatic indexing of code, docs, and tests into 135+ semantic chunks
- Natural language query interface for instant code documentation
- Terminal-based query system for codebase exploration

#### **Feature 3: Microservices Architecture Demo**
- Built event-driven architecture with message bus
- Created three independent microservices (Invoice, Ledger, Tax)
- Demonstrated loose coupling and async communication
- Event-based data flow for scalability
- Complete working prototype in `modernized-accounts/`

#### **Feature 4: VS Code Extension Integration**
- Developed full-featured VS Code extension for RAG system
- Interactive chat panel with beautiful UI
- Keyboard shortcuts (`Ctrl+Shift+R`, `Ctrl+Shift+E`)
- Right-click code explanation feature
- Configurable settings (API keys, models, Python path)
- Production-ready with 1,700+ lines of JavaScript code


### Future Ready

This refactoring prepares the codebase for:
- 🚀 **Microservices Architecture** - Services can be extracted independently
- 📡 **REST APIs** - Easy to expose service methods as endpoints
- 🔄 **Event-Driven Architecture** - Services can emit/consume events
- 📈 **Independent Scaling** - Scale specific services based on load

---

## 📁 Project Structure

```
Erpnext-Refactoring/
├── accounts/
│   ├── general_ledger.py              # Updated to use service layer
│   ├── services/                      # ✨ NEW: Service layer
│   │   ├── __init__.py
│   │   └── general_ledger_service.py  # Business logic extracted here
│   ├── party.py
│   ├── utils.py
│   └── ...
├── rag_system/                        # ✨ NEW: AI-powered RAG system
│   ├── rag_system.py                  # Main RAG implementation
│   ├── documents/                     # Comprehensive documentation
│   └── lancedb/                       # Vector database
├── vscode-rag-extension/              # ✨ NEW: VS Code Extension
│   ├── package.json                   # Extension manifest
│   ├── extension.js                   # Main extension code
│   ├── src/                           # Extension source files
│   │   ├── pythonBridge.js            # Python communication
│   │   └── chatPanel.js               # Chat WebView interface
│   └── README.md                      # Extension documentation
├── modernized-accounts/               # ✨ NEW: Microservices feature
│   ├── event_bus/                     # Event-driven architecture
│   ├── invoice-service/               # Invoice microservice
│   ├── ledger-service/                # Ledger microservice
│   └── tax-service/                   # Tax microservice
├── test_refactoring.py                # Automated test suite
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
└── .gitignore                         # Git ignore patterns
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ (for VS Code extension)
- Virtual environment (recommended)
- VS Code (for extension feature)

### Quick Setup

```bash
# 1. Navigate to project directory
cd Project-Directory

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 🎯 Feature-by-Feature Setup

### **Feature 1: Service Layer Refactoring**

```bash
# Run tests to verify refactoring
python test_refactoring.py
```

**Expected Output:**
```
✅ TEST 1: Basic GL Map Processing - PASSED
✅ TEST 2: Merging Similar Entries - PASSED
✅ TEST 3: Handling Negative Values - PASSED
✅ TEST 4: Backward Compatibility - PASSED
🎉 ALL TESTS PASSED!
```

### **Feature 2: RAG System**

```bash
# Configure API key in .env file
echo GROQ_API_KEY=your_key_here > .env

# Run RAG system
cd rag_system
python rag_system.py
```

**Try asking:**
- "What is the GeneralLedgerService?"
- "Explain the microservices architecture"

### **Feature 3: Microservices Demo**

```bash
cd modernized-accounts
python simple_demo.py
```

See complete architecture in action with event-driven invoice processing!

### **Feature 4: VS Code Extension**

```bash
# Navigate to extension folder
cd vscode-rag-extension

# Install Node.js dependencies
npm install

# Package extension
npm install -g vsce
vsce package

# Install in VS Code
code --install-extension erpnext-rag-assistant-1.0.0.vsix
```

**Configure & Use:**
1. Press `Ctrl+Shift+P` → "ERPNext RAG: Configure Groq API Key"
2. Press `Ctrl+Shift+R` to open chat
3. Ask questions directly in VS Code!

---

## 🤖 RAG System - AI-Powered Code Query

Query your refactored codebase with AI using LanceDB + Groq!

### Quick Setup

```bash
# 1. Install RAG dependencies (already in requirements.txt)
pip install -r requirements.txt

# 3. Configure API key in .env file
GROQ_API_KEY=your_actual_groq_api_key_here

# 4. Run the RAG system
cd rag_system
python rag_system.py
```

### What Gets Indexed?

The RAG system automatically indexes:
- 📚 **Documentation** (`rag_system/documents/`) - 4 comprehensive guides
- 💻 **Source Code** (`accounts/services/`) - Service layer implementation
- 📝 **Project Docs** - README guides
- 🧪 **Tests** - test_refactoring.py

### Example Questions

- "What is the GeneralLedgerService and what does it do?"
- "What are the main advantages of this refactoring?"
- "How does the merge_similar_entries function work?"
- "Explain the backward compatibility approach"
- "What tests are included and what do they verify?"
- "How does cost center distribution work?"
- "Show me how to test the GL processing"

### Architecture

```
User Question → Sentence Transformer → LanceDB → Groq LLM → AI Answer
```

### Features

✅ **100% Free Stack** - LanceDB + Sentence Transformers + Groq (free tier)
✅ **Fast** - 1-2 second response time
✅ **Private** - Embeddings run locally on your machine
✅ **Context-Aware** - Answers from YOUR actual codebase
✅ **Source Citations** - Shows which files were used

### RAG Documentation

Comprehensive documentation available in `rag_system/documents/`:
- [General Ledger Overview](rag_system/documents/general_ledger_overview.md) - Complete GL system guide
- [Service Layer Architecture](rag_system/documents/service_layer_architecture.md) - Refactoring details
- [Testing Guide](rag_system/documents/testing_guide.md) - Testing strategies
- [API Reference](rag_system/documents/api_reference.md) - Complete API docs

---

## 🔌 VS Code Extension - RAG Assistant

### Overview

The **ERPNext RAG Assistant** is a VS Code extension that brings the power of the RAG system directly into your IDE! Query your codebase without leaving VS Code.

### ✨ Features

- **💬 Interactive Chat Panel** - Ask questions in natural language
- **⌨️ Keyboard Shortcuts** - Quick access with `Ctrl+Shift+R`
- **📝 Explain Code** - Right-click selected code to get AI explanations
- **🔄 Auto-Indexing** - Automatically updates when files change
- **📚 Source Citations** - See which files were used for answers
- **⚙️ Configurable** - Customize models, API keys, and behavior

### Quick Start

#### 1. Install the Extension

```bash
# Navigate to extension folder
cd vscode-rag-extension

# Install Node.js dependencies
npm install

# Package the extension
npm install -g vsce
vsce package

# Install in VS Code
code --install-extension erpnext-rag-assistant-1.0.0.vsix
```

#### 2. Configure API Key

- Press `Ctrl+Shift+P` → Type `ERPNext RAG: Configure Groq API Key`
- Paste your API key from [console.groq.com](https://console.groq.com/)

#### 3. Start Using

- Press `Ctrl+Shift+R` to open the chat panel
- Ask questions about your codebase!

### Example Usage

```
💡 Open Chat Panel: Ctrl+Shift+R
💡 Explain Selected Code: Select code → Ctrl+Shift+E
💡 Re-index Workspace: Command Palette → "ERPNext RAG: Re-index Workspace"
```

### Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| ERPNext RAG: Open Chat | `Ctrl+Shift+R` | Open chat interface |
| ERPNext RAG: Explain Code | `Ctrl+Shift+E` | Explain selected code |
| ERPNext RAG: Re-index Workspace | - | Force re-index documents |
| ERPNext RAG: Clear History | - | Clear chat messages |
| ERPNext RAG: Configure API Key | - | Set Groq API key |

### Documentation

See the complete extension documentation: [vscode-rag-extension/README.md](vscode-rag-extension/README.md)

---

## 📬 Contact

For any queries or suggestions, feel free to reach out:

- 🏆 **LeetCode:** [leetcode.com/u/abinesh_06](https://leetcode.com/u/abinesh_06/)
- 📧 **Email:** abineshbalasubramaniyam@gmail.com
- 💼 **LinkedIn:** [linkedin.com/in/abiineshh](https://www.linkedin.com/in/abiineshh/)
- 🐙 **GitHub:** [github.com/Abinesh2418](https://github.com/Abinesh2418)
