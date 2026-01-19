# ERPNext RAG Assistant - VS Code Extension

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![VS Code](https://img.shields.io/badge/VS%20Code-%5E1.75.0-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**AI-powered code assistant for ERPNext refactoring with RAG (Retrieval-Augmented Generation) system integration**

## 🎯 Overview

This VS Code extension provides an intelligent chat interface to query your ERPNext refactoring project using RAG technology. Ask questions about your codebase and get instant, context-aware answers powered by LanceDB vector search and Groq's LLM.

### Key Features

✅ **AI Chat Interface** - Interactive sidebar panel for natural language queries  
✅ **Context-Aware Answers** - Searches your actual codebase for relevant information  
✅ **Code Explanation** - Right-click any code to get AI explanations  
✅ **Keyboard Shortcuts** - Quick access with `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)  
✅ **Auto-Indexing** - Automatically updates when files change  
✅ **Source Citations** - Shows which files were used to generate answers  
✅ **Free Technology Stack** - Uses LanceDB + Groq (free tier available)  

---

## 📸 Screenshots

### Chat Interface
```
┌─────────────────────────────────────┐
│  🤖 ERPNext RAG Assistant           │
├─────────────────────────────────────┤
│                                     │
│  You: What is GeneralLedgerService? │
│                                     │
│  Assistant: The GeneralLedgerService│
│  is a service class that encapsulates│
│  all business logic for general     │
│  ledger operations...               │
│  📚 Sources: general_ledger.py      │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Ask a question...           │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🚀 Installation

### Prerequisites

1. **VS Code** - Version 1.75.0 or higher
2. **Python** - Version 3.10 or higher
3. **Groq API Key** - Get free API key from [Groq Console](https://console.groq.com/)

### Installation Steps

#### Option 1: Install from VSIX (Recommended)

```bash
# Navigate to the extension folder
cd vscode-rag-extension

# Package the extension
npm install -g vsce
vsce package

# Install in VS Code
code --install-extension erpnext-rag-assistant-1.0.0.vsix
```

#### Option 2: Install from Source (Development)

```bash
# Navigate to the extension folder
cd vscode-rag-extension

# Install Node.js dependencies
npm install

# Link the extension for development
code --extensionDevelopmentPath=.
```

### Post-Installation Setup

1. **Install Python Dependencies**
   ```bash
   # From the workspace root
   pip install -r requirements.txt
   ```

2. **Configure Groq API Key**
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
   - Type: `ERPNext RAG: Configure Groq API Key`
   - Paste your API key from [console.groq.com](https://console.groq.com/)

3. **Open the Extension**
   - Press `Ctrl+Shift+R` or click the robot icon in the activity bar
   - Start asking questions!

---

## 📖 Usage Guide

### Opening the Chat Panel

**Method 1: Keyboard Shortcut**
- Windows/Linux: `Ctrl+Shift+R`
- Mac: `Cmd+Shift+R`

**Method 2: Command Palette**
- Press `Ctrl+Shift+P` / `Cmd+Shift+P`
- Type: `ERPNext RAG: Open Chat`

**Method 3: Activity Bar**
- Click the robot (🤖) icon in the left sidebar

### Example Questions

```
💡 "What is the GeneralLedgerService and what does it do?"
💡 "Explain the microservices architecture transformation"
💡 "How does the event bus work in the modernized system?"
💡 "What are the main advantages of this refactoring?"
💡 "Show me how to test the GL processing"
💡 "Explain the invoice service implementation"
```

### Explaining Selected Code

1. Select code in any file
2. Right-click → `ERPNext RAG: Explain Selected Code`
3. Or use keyboard shortcut: `Ctrl+Shift+E` / `Cmd+Shift+E`

The extension will open the chat panel and automatically query the RAG system about your selected code.

---

## ⚙️ Configuration

Access settings via: `File` → `Preferences` → `Settings` → Search for `ERPNext RAG`

| Setting | Default | Description |
|---------|---------|-------------|
| `erpnextRag.groqApiKey` | `""` | Groq API key for LLM responses |
| `erpnextRag.groqModel` | `llama-3.3-70b-versatile` | Groq LLM model to use |
| `erpnextRag.embeddingModel` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `erpnextRag.pythonPath` | `python` | Path to Python executable |
| `erpnextRag.autoIndex` | `true` | Auto re-index on file changes |
| `erpnextRag.maxResults` | `5` | Max context chunks to retrieve |

### Available Models

**Groq Models:**
- `llama-3.3-70b-versatile` (Recommended - Fast & Accurate)
- `llama-3.1-70b-versatile` (Alternative)
- `mixtral-8x7b-32768` (Longer context)

---

## 🎮 Commands

All commands available via Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

| Command | Shortcut | Description |
|---------|----------|-------------|
| `ERPNext RAG: Open Chat` | `Ctrl+Shift+R` | Open chat panel |
| `ERPNext RAG: Explain Selected Code` | `Ctrl+Shift+E` | Explain selected code |
| `ERPNext RAG: Re-index Workspace` | - | Force re-index all documents |
| `ERPNext RAG: Clear Chat History` | - | Clear all chat messages |
| `ERPNext RAG: Configure Groq API Key` | - | Set/update API key |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   VS Code Extension                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Chat UI    │  │  Commands    │  │   Settings   │  │
│  │  (WebView)   │  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                           │                             │
│                   ┌───────▼────────┐                    │
│                   │ Python Bridge  │                    │
│                   │ (Child Process)│                    │
│                   └───────┬────────┘                    │
└───────────────────────────┼─────────────────────────────┘
                            │
                    ┌───────▼─────────┐
                    │  RAG System     │
                    │  (Python)       │
                    ├─────────────────┤
                    │ • LanceDB       │
                    │ • Embeddings    │
                    │ • Groq LLM      │
                    └─────────────────┘
```

### Data Flow

1. **User Query** → Chat UI captures input
2. **Extension** → Sends query to Python Bridge
3. **Python Bridge** → Spawns Python process with RAG system
4. **RAG System** → 
   - Generates embedding for query
   - Searches LanceDB for relevant code chunks
   - Sends context + query to Groq LLM
5. **LLM Response** → Returned through Python → Bridge → UI
6. **Display** → Answer shown with source citations

---

## 📁 Project Structure

```
vscode-rag-extension/
│
├── package.json              # Extension manifest & metadata
├── extension.js              # Main extension entry point
├── README.md                 # This file
├── .vscodeignore            # Files to exclude from package
│
├── src/
│   ├── pythonBridge.js      # Python process communication
│   └── chatPanel.js         # WebView chat interface
│
└── media/
    ├── icon.png             # Extension icon
    └── styles.css           # Additional styles (optional)
```

---

## 🔧 Development

### Running in Development Mode

```bash
# Install dependencies
npm install

# Open VS Code with extension
code .

# Press F5 to launch Extension Development Host
# The extension will be loaded in a new VS Code window
```

### Debugging

1. Set breakpoints in JavaScript files
2. Press `F5` to start debugging
3. Check Debug Console for logs
4. View Python output in "ERPNext RAG" output channel

### Building VSIX Package

```bash
# Install vsce globally
npm install -g vsce

# Package extension
vsce package

# Output: erpnext-rag-assistant-1.0.0.vsix
```

---

## 🐛 Troubleshooting

### Issue: "Required Python packages not installed"

**Solution:**
```bash
cd /path/to/workspace
pip install -r requirements.txt
```

### Issue: "Groq API key not configured"

**Solution:**
1. Get API key from [console.groq.com](https://console.groq.com/)
2. Run command: `ERPNext RAG: Configure Groq API Key`
3. Paste your API key

### Issue: "Python not found"

**Solution:**
1. Verify Python installation: `python --version`
2. Update setting: `erpnextRag.pythonPath`
3. Set to full path: `C:\Python310\python.exe` or `/usr/bin/python3`

### Issue: Extension not loading

**Solution:**
1. Check VS Code version (must be 1.75.0+)
2. View output: `View` → `Output` → Select "ERPNext RAG"
3. Reload window: `Ctrl+R` / `Cmd+R`

### Issue: RAG system slow to respond

**Solution:**
- First query is slow (loading models)
- Subsequent queries are faster (cached)
- Reduce `maxResults` setting for faster queries
- Use a smaller embedding model

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| First Query (Cold Start) | ~3-5 seconds |
| Subsequent Queries | ~1-2 seconds |
| Memory Usage | ~200-300 MB |
| Extension Size | ~50 KB |
| Index Size | Varies by project |

---

## 🔐 Privacy & Security

- ✅ **Embeddings generated locally** - No code sent to external servers
- ✅ **API key stored securely** - VS Code's secure storage
- ✅ **LanceDB is local** - Vector database on your machine
- ⚠️ **Only queries sent to Groq** - Not full code, only search results
- ⚠️ **Free Groq tier** - Subject to rate limits

---

## 🤝 Contributing

Contributions welcome! Areas to improve:

- [ ] Add support for more LLM providers (OpenAI, Anthropic)
- [ ] Implement streaming responses
- [ ] Add code generation features
- [ ] Support multiple programming languages
- [ ] Add inline code suggestions
- [ ] Improve embedding models
- [ ] Add conversation memory

---

## 📋 Changelog

### Version 1.0.0 (2026-01-19)

**Initial Release**
- ✨ Interactive chat interface
- ✨ Code explanation feature
- ✨ Auto-indexing support
- ✨ Keyboard shortcuts
- ✨ Configurable settings
- ✨ Source citations
- ✨ Chat history

---


## 🙏 Acknowledgments

- **LanceDB** - Fast vector database
- **Sentence Transformers** - High-quality embeddings
- **Groq** - Lightning-fast LLM inference
- **VS Code Team** - Excellent extension API

---

**Happy Coding! 🚀**
