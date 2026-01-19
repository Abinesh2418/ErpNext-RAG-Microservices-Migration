#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query script for ERPNext RAG system - VS Code Extension Integration
Suppresses verbose output and returns only JSON
"""
import sys
import json
import os
from io import StringIO

class SilentOutput(StringIO):
    """StringIO wrapper that supports reconfigure() method"""
    def reconfigure(self, **kwargs):
        pass  # Ignore reconfigure calls
    
    def flush(self):
        pass  # Ignore flush calls

def main():
    if len(sys.argv) < 2:
        result = {"error": "No query provided"}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)
    
    query = sys.argv[1]
    
    # Save original stdout/stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    try:
        # Redirect to silent output that supports reconfigure()
        sys.stdout = SilentOutput()
        sys.stderr = SilentOutput()
        
        # Import and initialize RAG system (silently)
        from rag_system import ERPNextRAG
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        embedding_model = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        
        # Initialize RAG system
        rag = ERPNextRAG(groq_api_key=groq_api_key, embedding_model_name=embedding_model)
        
        # Query the system
        result = rag.ask(query)
        
        # Restore stdout to output JSON
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Format and output response as JSON
        response = {
            "answer": result if result else "No answer generated",
            "sources": []
        }
        
        # Output clean JSON only
        print(json.dumps(response, ensure_ascii=False))
        sys.exit(0)
        
    except Exception as e:
        # Restore stdout/stderr for error output
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Format error message safely
        error_message = str(e).replace('"', "'")
        result = {"error": error_message}
        
        # Output error as JSON to stderr
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
