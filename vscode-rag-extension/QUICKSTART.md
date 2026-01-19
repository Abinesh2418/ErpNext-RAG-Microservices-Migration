# Quick Start Guide - VS Code Extension

This guide helps you quickly install and test the ERPNext RAG Assistant extension.

## 🚀 Quick Installation

### Step 1: Install Node.js Dependencies

```bash
cd vscode-rag-extension
npm install
```

### Step 2: Package the Extension

```bash
# Install vsce (Visual Studio Code Extension CLI)
npm install -g vsce

# Package the extension
vsce package
```

This creates: `erpnext-rag-assistant-1.0.0.vsix`

### Step 3: Install in VS Code

**Option A: Command Line**
```bash
code --install-extension erpnext-rag-assistant-1.0.0.vsix
```

**Option B: VS Code UI**
1. Open VS Code
2. Press `Ctrl+Shift+X` (Extensions view)
3. Click the `...` menu → `Install from VSIX...`
4. Select `erpnext-rag-assistant-1.0.0.vsix`

### Step 4: Configure

1. Press `Ctrl+Shift+P`
2. Type: `ERPNext RAG: Configure Groq API Key`
3. Paste your API key from [console.groq.com](https://console.groq.com/)

### Step 5: Test!

1. Press `Ctrl+Shift+R` to open chat
2. Ask: "What is the GeneralLedgerService?"
3. Get instant AI-powered answers!

---

## 🧪 Development Mode (Testing Changes)

If you're modifying the extension code:

```bash
# Navigate to extension folder
cd vscode-rag-extension

# Open in VS Code
code .

# Press F5 to launch Extension Development Host
# A new VS Code window opens with your extension loaded
```

Make changes → Save → Reload window (`Ctrl+R`) → Test!

---

## 📋 Verification Checklist

After installation, verify everything works:

- [ ] Extension appears in Extensions view
- [ ] Robot icon (🤖) appears in activity bar
- [ ] `Ctrl+Shift+R` opens chat panel
- [ ] Commands appear in Command Palette (`Ctrl+Shift+P`)
- [ ] Python dependencies installed (`pip list`)
- [ ] Groq API key configured
- [ ] Can send a test query and get response

---

## 🐛 Common Issues

### "Command 'vsce' not found"

```bash
npm install -g vsce
# If permission error on Linux/Mac:
sudo npm install -g vsce
```

### "Extension not loading"

1. Check VS Code version: `Help` → `About`
   - Must be 1.75.0 or higher
2. Check Output: `View` → `Output` → Select "ERPNext RAG"
3. Reload window: `Ctrl+R`

### "Python dependencies not found"

```bash
# From workspace root
cd ..
pip install -r requirements.txt
```

### "Groq API rate limit"

- Free tier: 30 requests/minute
- Wait 60 seconds or upgrade at console.groq.com

---

## 📦 Publishing (Optional)

To publish to VS Code Marketplace:

1. Create publisher account at [marketplace.visualstudio.com](https://marketplace.visualstudio.com/)
2. Get Personal Access Token
3. Login: `vsce login your-publisher-name`
4. Publish: `vsce publish`

---

## 🎯 Next Steps

- Customize settings in VS Code settings (`File` → `Preferences` → `Settings`)
- Try explaining selected code with `Ctrl+Shift+E`
- Re-index workspace with `ERPNext RAG: Re-index Workspace`
- Check extension logs in Output panel

---

## 📚 Resources

- [Extension README](README.md) - Full documentation
- [VS Code Extension API](https://code.visualstudio.com/api)
- [Groq Documentation](https://console.groq.com/docs)
- [LanceDB Docs](https://lancedb.github.io/lancedb/)

---

**Enjoy coding with AI assistance! 🚀**
