const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Bridge between VS Code extension and Python RAG system
 */
class PythonBridge {
    constructor(ragSystemPath, outputChannel) {
        this.ragSystemPath = ragSystemPath;
        this.outputChannel = outputChannel;
        this.pythonProcess = null;
        this.queryQueue = [];
        this.isProcessing = false;
    }
    
    /**
     * Get Python path from configuration
     */
    getPythonPath() {
        const config = vscode.workspace.getConfiguration('erpnextRag');
        return config.get('pythonPath', 'python');
    }
    
    /**
     * Get configuration for RAG system
     */
    getConfig() {
        const config = vscode.workspace.getConfiguration('erpnextRag');
        return {
            groqApiKey: config.get('groqApiKey', ''),
            groqModel: config.get('groqModel', 'llama-3.3-70b-versatile'),
            embeddingModel: config.get('embeddingModel', 'all-MiniLM-L6-v2'),
            maxResults: config.get('maxResults', 5)
        };
    }
    
    /**
     * Check if Python dependencies are installed
     */
    async checkDependencies() {
        return new Promise((resolve, reject) => {
            const pythonPath = this.getPythonPath();
            const process = spawn(pythonPath, ['-c', 
                'import lancedb, sentence_transformers, groq, langchain_text_splitters; print("OK")'
            ]);
            
            let output = '';
            process.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            process.stderr.on('data', (data) => {
                this.outputChannel.appendLine(`Dependency check stderr: ${data}`);
            });
            
            process.on('close', (code) => {
                if (code === 0 && output.includes('OK')) {
                    resolve(true);
                } else {
                    reject(new Error('Required Python packages not installed'));
                }
            });
            
            process.on('error', (err) => {
                reject(new Error(`Python not found: ${err.message}`));
            });
        });
    }
    
    /**
     * Query the RAG system
     * @param {string} query - User question
     * @returns {Promise<{answer: string, sources: string[]}>}
     */
    async query(query) {
        const config = this.getConfig();
        
        if (!config.groqApiKey) {
            throw new Error('Groq API key not configured. Use "ERPNext RAG: Configure Groq API Key" command.');
        }
        
        return new Promise((resolve, reject) => {
            const pythonPath = this.getPythonPath();
            const scriptPath = path.join(this.ragSystemPath, 'rag_query.py');
            
            // Create a temporary query script if it doesn't exist
            this.ensureQueryScript();
            
            const env = {
                ...process.env,
                GROQ_API_KEY: config.groqApiKey,
                GROQ_MODEL: config.groqModel,
                EMBEDDING_MODEL: config.embeddingModel,
                MAX_RESULTS: config.maxResults.toString()
            };
            
            this.outputChannel.appendLine(`Querying RAG system: "${query.substring(0, 50)}..."`);
            
            const pythonProcess = spawn(pythonPath, [scriptPath, query], {
                cwd: this.ragSystemPath,
                env: env
            });
            
            let stdout = '';
            let stderr = '';
            
            pythonProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            pythonProcess.stderr.on('data', (data) => {
                stderr += data.toString();
                this.outputChannel.appendLine(`Python stderr: ${data}`);
            });
            
            pythonProcess.on('close', (code) => {
                if (code === 0) {
                    try {
                        // Parse JSON response
                        const response = JSON.parse(stdout);
                        this.outputChannel.appendLine('Query successful');
                        resolve(response);
                    } catch (err) {
                        this.outputChannel.appendLine(`Parse error: ${err.message}`);
                        this.outputChannel.appendLine(`Output: ${stdout}`);
                        reject(new Error(`Failed to parse response: ${err.message}`));
                    }
                } else {
                    this.outputChannel.appendLine(`Process exited with code ${code}`);
                    reject(new Error(`Query failed: ${stderr || 'Unknown error'}`));
                }
            });
            
            pythonProcess.on('error', (err) => {
                this.outputChannel.appendLine(`Process error: ${err.message}`);
                reject(new Error(`Failed to execute Python: ${err.message}`));
            });
        });
    }
    
    /**
     * Re-index the workspace
     */
    async reindex() {
        return new Promise((resolve, reject) => {
            const pythonPath = this.getPythonPath();
            const scriptPath = path.join(this.ragSystemPath, 'rag_reindex.py');
            
            this.ensureReindexScript();
            
            const config = this.getConfig();
            const env = {
                ...process.env,
                EMBEDDING_MODEL: config.embeddingModel
            };
            
            this.outputChannel.appendLine('Starting re-indexing...');
            
            const pythonProcess = spawn(pythonPath, [scriptPath], {
                cwd: this.ragSystemPath,
                env: env
            });
            
            pythonProcess.stdout.on('data', (data) => {
                this.outputChannel.appendLine(data.toString());
            });
            
            pythonProcess.stderr.on('data', (data) => {
                this.outputChannel.appendLine(data.toString());
            });
            
            pythonProcess.on('close', (code) => {
                if (code === 0) {
                    this.outputChannel.appendLine('Re-indexing completed');
                    resolve();
                } else {
                    reject(new Error('Re-indexing failed'));
                }
            });
            
            pythonProcess.on('error', (err) => {
                reject(new Error(`Failed to execute Python: ${err.message}`));
            });
        });
    }
    
    /**
     * Ensure query script exists
     */
    ensureQueryScript() {
        const scriptPath = path.join(this.ragSystemPath, 'rag_query.py');
        
        if (!fs.existsSync(scriptPath)) {
            const script = `#!/usr/bin/env python3
import sys
import json
import os
from rag_system import ERPNextRAG

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided"}))
        sys.exit(1)
    
    query = sys.argv[1]
    
    try:
        # Initialize RAG system
        groq_api_key = os.getenv('GROQ_API_KEY')
        embedding_model = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        
        rag = ERPNextRAG(groq_api_key=groq_api_key, embedding_model_name=embedding_model)
        
        # Query
        result = rag.query(query)
        
        # Format response
        response = {
            "answer": result,
            "sources": []
        }
        
        print(json.dumps(response))
        sys.exit(0)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
`;
            fs.writeFileSync(scriptPath, script);
            this.outputChannel.appendLine('Created rag_query.py script');
        }
    }
    
    /**
     * Ensure reindex script exists
     */
    ensureReindexScript() {
        const scriptPath = path.join(this.ragSystemPath, 'rag_reindex.py');
        
        if (!fs.existsSync(scriptPath)) {
            const script = `#!/usr/bin/env python3
import os
from rag_system import ERPNextRAG

def main():
    try:
        embedding_model = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        rag = ERPNextRAG(groq_api_key='dummy', embedding_model_name=embedding_model)
        print("Re-indexing completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
`;
            fs.writeFileSync(scriptPath, script);
            this.outputChannel.appendLine('Created rag_reindex.py script');
        }
    }
    
    /**
     * Dispose resources
     */
    dispose() {
        if (this.pythonProcess) {
            this.pythonProcess.kill();
        }
    }
}

module.exports = { PythonBridge };
