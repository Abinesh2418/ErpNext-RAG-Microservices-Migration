const vscode = require('vscode');
const path = require('path');

/**
 * WebView panel for chat interface
 */
class ChatPanel {
    constructor(extensionUri, pythonBridge, outputChannel) {
        this.extensionUri = extensionUri;
        this.pythonBridge = pythonBridge;
        this.outputChannel = outputChannel;
        this.panel = null;
        this.chatHistory = [];
    }
    
    /**
     * Show or create the chat panel
     */
    show() {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.Two);
            return;
        }
        
        this.panel = vscode.window.createWebviewPanel(
            'erpnextRagChat',
            'ERPNext RAG Assistant',
            vscode.ViewColumn.Two,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.extensionUri, 'media')
                ]
            }
        );
        
        this.panel.webview.html = this.getWebviewContent();
        
        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.type) {
                    case 'query':
                        await this.handleQuery(message.query);
                        break;
                    case 'clear':
                        this.clearHistory();
                        break;
                }
            }
        );
        
        // Reset panel when disposed
        this.panel.onDidDispose(() => {
            this.panel = null;
        });
        
        // Load history
        this.loadHistory();
    }
    
    /**
     * Handle user query
     */
    async handleQuery(query) {
        if (!query || !query.trim()) {
            return;
        }
        
        // Add user message to history
        this.addMessage('user', query);
        
        // Show loading state
        this.panel.webview.postMessage({
            type: 'loading',
            loading: true
        });
        
        try {
            // Query RAG system
            const response = await this.pythonBridge.query(query);
            
            // Add assistant response
            this.addMessage('assistant', response.answer, response.sources);
            
        } catch (error) {
            this.outputChannel.appendLine(`Query error: ${error.message}`);
            
            const errorMessage = error.message.includes('API key') 
                ? '⚠️ Please configure your Groq API key using the "ERPNext RAG: Configure Groq API Key" command.'
                : `❌ Error: ${error.message}`;
            
            this.addMessage('error', errorMessage);
        } finally {
            this.panel.webview.postMessage({
                type: 'loading',
                loading: false
            });
        }
    }
    
    /**
     * Add message to chat history
     */
    addMessage(role, content, sources = []) {
        const message = {
            role,
            content,
            sources,
            timestamp: new Date().toISOString()
        };
        
        this.chatHistory.push(message);
        
        if (this.panel) {
            this.panel.webview.postMessage({
                type: 'message',
                message
            });
        }
    }
    
    /**
     * Send query programmatically
     */
    async sendQuery(query) {
        if (this.panel) {
            this.panel.webview.postMessage({
                type: 'setQuery',
                query
            });
            await this.handleQuery(query);
        }
    }
    
    /**
     * Clear chat history
     */
    clearHistory() {
        this.chatHistory = [];
        if (this.panel) {
            this.panel.webview.postMessage({
                type: 'clearHistory'
            });
        }
    }
    
    /**
     * Load history into webview
     */
    loadHistory() {
        if (this.panel && this.chatHistory.length > 0) {
            this.panel.webview.postMessage({
                type: 'loadHistory',
                history: this.chatHistory
            });
        }
    }
    
    /**
     * Generate webview HTML content
     */
    getWebviewContent() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERPNext RAG Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        #header {
            padding: 16px;
            background-color: var(--vscode-sideBar-background);
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        #header h1 {
            font-size: 18px;
            font-weight: 600;
        }
        
        #clear-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        #clear-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        
        .message {
            margin-bottom: 16px;
            padding: 12px;
            border-radius: 8px;
            max-width: 85%;
            word-wrap: break-word;
        }
        
        .message.user {
            background-color: var(--vscode-input-background);
            margin-left: auto;
            border: 1px solid var(--vscode-input-border);
        }
        
        .message.assistant {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            margin-right: auto;
        }
        
        .message.error {
            background-color: var(--vscode-inputValidation-errorBackground);
            border: 1px solid var(--vscode-inputValidation-errorBorder);
            margin-right: auto;
        }
        
        .message-header {
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 12px;
            opacity: 0.8;
        }
        
        .message-content {
            line-height: 1.6;
            white-space: pre-wrap;
        }
        
        .sources {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--vscode-panel-border);
            font-size: 12px;
        }
        
        .sources-title {
            font-weight: 600;
            margin-bottom: 6px;
            opacity: 0.8;
        }
        
        .source-item {
            margin: 4px 0;
            color: var(--vscode-textLink-foreground);
            cursor: pointer;
        }
        
        .source-item:hover {
            text-decoration: underline;
        }
        
        #input-container {
            padding: 16px;
            background-color: var(--vscode-sideBar-background);
            border-top: 1px solid var(--vscode-panel-border);
        }
        
        #input-form {
            display: flex;
            gap: 8px;
        }
        
        #query-input {
            flex: 1;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            padding: 10px;
            border-radius: 4px;
            font-family: inherit;
            font-size: inherit;
            resize: none;
        }
        
        #query-input:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }
        
        #send-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
        }
        
        #send-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        #send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 16px;
            font-style: italic;
            opacity: 0.7;
        }
        
        .loading.active {
            display: block;
        }
        
        .welcome {
            text-align: center;
            padding: 40px 20px;
            opacity: 0.7;
        }
        
        .welcome h2 {
            margin-bottom: 16px;
        }
        
        .example-queries {
            margin-top: 24px;
            text-align: left;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .example-query {
            background: var(--vscode-input-background);
            padding: 8px 12px;
            margin: 8px 0;
            border-radius: 4px;
            cursor: pointer;
            border: 1px solid var(--vscode-input-border);
        }
        
        .example-query:hover {
            background: var(--vscode-list-hoverBackground);
        }
        
        code {
            background: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>🤖 ERPNext RAG Assistant</h1>
        <button id="clear-btn">Clear History</button>
    </div>
    
    <div id="chat-container">
        <div class="welcome">
            <h2>👋 Welcome to ERPNext RAG Assistant!</h2>
            <p>Ask me anything about the ERPNext refactoring project.</p>
            
            <div class="example-queries">
                <strong>Example questions:</strong>
                <div class="example-query" data-query="What is the GeneralLedgerService and what does it do?">
                    💡 What is the GeneralLedgerService and what does it do?
                </div>
                <div class="example-query" data-query="Explain the microservices architecture transformation">
                    💡 Explain the microservices architecture transformation
                </div>
                <div class="example-query" data-query="How does the event bus work in the modernized system?">
                    💡 How does the event bus work in the modernized system?
                </div>
                <div class="example-query" data-query="What are the main advantages of this refactoring?">
                    💡 What are the main advantages of this refactoring?
                </div>
            </div>
        </div>
        <div class="loading">🔄 Thinking...</div>
    </div>
    
    <div id="input-container">
        <form id="input-form">
            <textarea 
                id="query-input" 
                placeholder="Ask a question about the ERPNext codebase..."
                rows="2"
            ></textarea>
            <button type="submit" id="send-btn">Send</button>
        </form>
    </div>
    
    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chat-container');
        const queryInput = document.getElementById('query-input');
        const sendBtn = document.getElementById('send-btn');
        const clearBtn = document.getElementById('clear-btn');
        const inputForm = document.getElementById('input-form');
        const loading = document.querySelector('.loading');
        const welcome = document.querySelector('.welcome');
        
        // Handle form submission
        inputForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = queryInput.value.trim();
            if (query) {
                vscode.postMessage({
                    type: 'query',
                    query: query
                });
                queryInput.value = '';
                hideWelcome();
            }
        });
        
        // Handle clear button
        clearBtn.addEventListener('click', () => {
            vscode.postMessage({ type: 'clear' });
        });
        
        // Handle example queries
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('example-query')) {
                const query = e.target.getAttribute('data-query');
                queryInput.value = query;
                inputForm.dispatchEvent(new Event('submit'));
            }
        });
        
        // Handle Enter key (Shift+Enter for new line)
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                inputForm.dispatchEvent(new Event('submit'));
            }
        });
        
        // Receive messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'message':
                    addMessage(message.message);
                    break;
                case 'loading':
                    setLoading(message.loading);
                    break;
                case 'clearHistory':
                    clearMessages();
                    break;
                case 'loadHistory':
                    loadHistory(message.history);
                    break;
                case 'setQuery':
                    queryInput.value = message.query;
                    break;
            }
        });
        
        function hideWelcome() {
            if (welcome) {
                welcome.style.display = 'none';
            }
        }
        
        function addMessage(msg) {
            hideWelcome();
            
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${msg.role}\`;
            
            const header = document.createElement('div');
            header.className = 'message-header';
            header.textContent = msg.role === 'user' ? 'You' : 
                                msg.role === 'error' ? 'Error' : 'Assistant';
            
            const content = document.createElement('div');
            content.className = 'message-content';
            content.textContent = msg.content;
            
            messageDiv.appendChild(header);
            messageDiv.appendChild(content);
            
            // Add sources if available
            if (msg.sources && msg.sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                
                const sourcesTitle = document.createElement('div');
                sourcesTitle.className = 'sources-title';
                sourcesTitle.textContent = '📚 Sources:';
                sourcesDiv.appendChild(sourcesTitle);
                
                msg.sources.forEach(source => {
                    const sourceItem = document.createElement('div');
                    sourceItem.className = 'source-item';
                    sourceItem.textContent = \`• \${source}\`;
                    sourcesDiv.appendChild(sourceItem);
                });
                
                messageDiv.appendChild(sourcesDiv);
            }
            
            chatContainer.insertBefore(messageDiv, loading);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function setLoading(isLoading) {
            loading.classList.toggle('active', isLoading);
            sendBtn.disabled = isLoading;
            queryInput.disabled = isLoading;
            
            if (isLoading) {
                hideWelcome();
            }
        }
        
        function clearMessages() {
            const messages = chatContainer.querySelectorAll('.message');
            messages.forEach(msg => msg.remove());
            if (welcome) {
                welcome.style.display = 'block';
            }
        }
        
        function loadHistory(history) {
            history.forEach(msg => addMessage(msg));
        }
    </script>
</body>
</html>`;
    }
}

module.exports = { ChatPanel };
