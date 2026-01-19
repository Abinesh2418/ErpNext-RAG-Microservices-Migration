const vscode = require('vscode');
const path = require('path');
const { PythonBridge } = require('./src/pythonBridge');
const { ChatPanel } = require('./src/chatPanel');

let pythonBridge;
let chatPanel;
let outputChannel;

/**
 * Extension activation
 * @param {vscode.ExtensionContext} context
 */
async function activate(context) {
    console.log('ERPNext RAG Assistant is now active!');
    
    // Create output channel for logs
    outputChannel = vscode.window.createOutputChannel('ERPNext RAG');
    outputChannel.appendLine('ERPNext RAG Assistant activated');
    
    // Initialize Python bridge
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showWarningMessage('ERPNext RAG: No workspace folder open');
        return;
    }
    
    const ragSystemPath = path.join(workspaceFolder.uri.fsPath, 'rag_system');
    pythonBridge = new PythonBridge(ragSystemPath, outputChannel);
    
    // Initialize chat panel
    chatPanel = new ChatPanel(context.extensionUri, pythonBridge, outputChannel);
    
    // Register commands
    
    // Open Chat Panel
    context.subscriptions.push(
        vscode.commands.registerCommand('erpnext-rag.openChat', () => {
            chatPanel.show();
        })
    );
    
    // Explain Selected Code
    context.subscriptions.push(
        vscode.commands.registerCommand('erpnext-rag.explainCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor');
                return;
            }
            
            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);
            
            if (!selectedText) {
                vscode.window.showWarningMessage('No code selected');
                return;
            }
            
            const fileName = path.basename(editor.document.fileName);
            const query = `Explain this code from ${fileName}:\n\n${selectedText}`;
            
            chatPanel.show();
            chatPanel.sendQuery(query);
        })
    );
    
    // Re-index Workspace
    context.subscriptions.push(
        vscode.commands.registerCommand('erpnext-rag.indexWorkspace', async () => {
            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Re-indexing workspace...",
                cancellable: false
            }, async () => {
                try {
                    outputChannel.appendLine('Starting workspace re-indexing...');
                    await pythonBridge.reindex();
                    vscode.window.showInformationMessage('Workspace re-indexed successfully!');
                    outputChannel.appendLine('Re-indexing completed');
                } catch (error) {
                    vscode.window.showErrorMessage(`Re-indexing failed: ${error.message}`);
                    outputChannel.appendLine(`Re-indexing error: ${error.message}`);
                }
            });
        })
    );
    
    // Clear Chat History
    context.subscriptions.push(
        vscode.commands.registerCommand('erpnext-rag.clearHistory', () => {
            chatPanel.clearHistory();
            vscode.window.showInformationMessage('Chat history cleared');
        })
    );
    
    // Configure API Key
    context.subscriptions.push(
        vscode.commands.registerCommand('erpnext-rag.configureApiKey', async () => {
            const config = vscode.workspace.getConfiguration('erpnextRag');
            const currentKey = config.get('groqApiKey', '');
            
            const newKey = await vscode.window.showInputBox({
                prompt: 'Enter your Groq API key',
                password: true,
                value: currentKey,
                placeHolder: 'gsk_...',
                ignoreFocusOut: true
            });
            
            if (newKey !== undefined) {
                await config.update('groqApiKey', newKey, vscode.ConfigurationTarget.Global);
                vscode.window.showInformationMessage('Groq API key saved successfully!');
                outputChannel.appendLine('API key updated');
            }
        })
    );
    
    // Auto-open chat panel on first activation
    const hasShownWelcome = context.globalState.get('hasShownWelcome', false);
    if (!hasShownWelcome) {
        chatPanel.show();
        context.globalState.update('hasShownWelcome', true);
    }
    
    // Check for Python and dependencies
    setTimeout(async () => {
        try {
            await pythonBridge.checkDependencies();
            outputChannel.appendLine('Python dependencies verified');
        } catch (error) {
            vscode.window.showWarningMessage(
                `ERPNext RAG: ${error.message}. Run 'pip install -r requirements.txt' to fix.`,
                'Open Terminal'
            ).then(selection => {
                if (selection === 'Open Terminal') {
                    const terminal = vscode.window.createTerminal('ERPNext RAG Setup');
                    terminal.show();
                    terminal.sendText(`cd "${workspaceFolder.uri.fsPath}"`);
                    terminal.sendText('pip install -r requirements.txt');
                }
            });
        }
    }, 2000);
    
    outputChannel.appendLine('All commands registered successfully');
}

/**
 * Extension deactivation
 */
function deactivate() {
    if (pythonBridge) {
        pythonBridge.dispose();
    }
    if (outputChannel) {
        outputChannel.dispose();
    }
}

module.exports = {
    activate,
    deactivate
};
