"""
AI Converter
Converts Python Accounts code to Go using AI (Groq API)
"""

import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Optional import - groq may not be available
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_AVAILABLE = False


class AIConverter:
    """AI-powered Python to Go converter"""
    
    def __init__(self, config, logger):
        """
        Initialize AI converter
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.groq_client = None
        self.conversion_report_file = None
        self.conversion_warnings = []
        
        # Initialize Groq client
        api_key = self.config.get('GROQ_API_KEY')
        if not GROQ_AVAILABLE:
            self.groq_client = None
            self.logger.warning("Groq package not installed - using template conversion fallback")
        elif api_key:
            try:
                self.groq_client = Groq(api_key=api_key)
                self.logger.info("Groq AI client initialized successfully")
            except Exception as e:
                self.groq_client = None
                self.logger.warning(f"Failed to initialize Groq client: {e}")
        else:
            self.groq_client = None
            self.logger.warning("GROQ_API_KEY not set - using template conversion fallback")
    
    def convert(self, context: Dict[str, Any], files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert Python files to Go
        
        Args:
            context: Prepared context from dependency analyzer
            files: List of file information from scanner
            
        Returns:
            Conversion results dictionary
        """
        from ..utils.logger import get_timestamped_filename
        
        self.logger.info(f"Starting AI conversion for {len(files)} files")
        
        # Create results directory
        results_dir = self.config.get('RESULTS_DIR')
        self.conversion_report_file = results_dir / get_timestamped_filename('conversion_report', 'txt')
        
        modern_dir = self.config.get('MODERN_DIR')
        
        converted_modules = []
        
        # Convert each file
        for file_info in files:
            if not file_info.get('valid_syntax', False):
                self.logger.warning(f"Skipping invalid file: {file_info['name']}")
                continue
            
            try:
                go_code = self._convert_file(file_info, context)
                
                if go_code:
                    # Determine Go module structure
                    go_module = self._determine_go_module(file_info['name'])
                    go_dir = modern_dir / go_module
                    go_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Write Go file
                    go_file = go_dir / f"{Path(file_info['name']).stem}.go"
                    with open(go_file, 'w', encoding='utf-8') as f:
                        f.write(go_code)
                    
                    converted_modules.append({
                        'python_file': file_info['name'],
                        'go_file': str(go_file),
                        'module': go_module
                    })
                    
                    self.logger.info(f"Converted: {file_info['name']} → {go_file.name}")
                    
            except Exception as e:
                self.logger.error(f"Failed to convert {file_info['name']}: {e}")
                self.conversion_warnings.append({
                    'file': file_info['name'],
                    'error': str(e)
                })
        
        # Write conversion report
        self._write_conversion_report(converted_modules, context)
        
        result = {
            'modules_created': len(converted_modules),
            'warnings': len(self.conversion_warnings),
            'converted_modules': converted_modules,
            'report_file': str(self.conversion_report_file),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Conversion complete: {len(converted_modules)} modules created")
        return result
    
    def _convert_file(self, file_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Convert single Python file to Go
        
        Args:
            file_info: File information dictionary
            context: Context information
            
        Returns:
            Go code as string
        """
        file_path = Path(file_info['path'])
        
        # Read Python code
        with open(file_path, 'r', encoding='utf-8') as f:
            python_code = f.read()
        
        # If AI is available, use it
        if self.groq_client:
            return self._ai_convert(python_code, file_info, context)
        else:
            return self._template_convert(python_code, file_info)
    
    def _ai_convert(self, python_code: str, file_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Convert using AI (Groq)
        
        Args:
            python_code: Python source code
            file_info: File information
            context: Context information
            
        Returns:
            Go code as string
        """
        try:
            # Build conversion prompt
            prompt = self._build_conversion_prompt(python_code, file_info, context)
            
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model=self.config.get('GROQ_MODEL'),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in converting Python accounting/ERP code to Go. "
                                   "Preserve business logic, accounting rules, and data integrity. "
                                   "Generate idiomatic Go code with proper error handling."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.get('AI_TEMPERATURE'),
                max_tokens=4000
            )
            
            go_code = response.choices[0].message.content
            
            # Extract Go code from markdown if present
            if "```go" in go_code:
                go_code = go_code.split("```go")[1].split("```")[0].strip()
            elif "```" in go_code:
                go_code = go_code.split("```")[1].split("```")[0].strip()
            
            return go_code
            
        except Exception as e:
            self.logger.error(f"AI conversion failed: {e}")
            self.conversion_warnings.append({
                'file': file_info['name'],
                'error': f"AI conversion failed: {str(e)}",
                'fallback': 'template'
            })
            return self._template_convert(python_code, file_info)
    
    def _template_convert(self, python_code: str, file_info: Dict[str, Any]) -> str:
        """
        Template-based conversion (fallback when AI not available)
        
        Args:
            python_code: Python source code
            file_info: File information
            
        Returns:
            Go code template as string
        """
        module_name = Path(file_info['name']).stem
        
        go_template = f"""package {self._determine_go_module(file_info['name'])}

// Converted from: {file_info['name']}
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// NOTE: This is a template conversion. Manual review required.

import (
	"fmt"
	"time"
)

// TODO: Implement conversion from Python
// Original Python file: {file_info['path']}
// Lines: {file_info.get('lines', 'N/A')}

// Placeholder structure
type {module_name.title().replace('_', '')} struct {{
	// TODO: Add fields from Python class
}}

// TODO: Convert Python functions to Go methods
func New{module_name.title().replace('_', '')}() *{module_name.title().replace('_', '')} {{
	return &{module_name.title().replace('_', '')}{{}}
}}

// Example method - replace with actual conversions
func (m *{module_name.title().replace('_', '')}) Process() error {{
	// TODO: Implement business logic from Python
	fmt.Println("Method not yet implemented")
	return nil
}}
"""
        
        return go_template
    
    def _build_conversion_prompt(self, python_code: str, file_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build prompt for AI conversion"""
        prompt = f"""Convert the following Python ERPNext Accounts module code to Go.

Context:
- This is part of an accounting/ERP system
- Business domains: {', '.join(context.get('business_domains', []))}
- File: {file_info['name']}
- The code handles accounting operations like ledger entries, invoices, taxes, etc.

Requirements:
1. Preserve all accounting business logic exactly
2. Maintain data integrity and validation rules
3. Use Go idioms (interfaces, error handling, struct composition)
4. Add proper error handling for all operations
5. Include comments explaining accounting logic
6. Flag any unclear or complex business rules with TODO comments

Python Code:
```python
{python_code[:3000]}  # Truncated for context limit
```

Generate complete, production-ready Go code. Include package declaration, imports, structs, and methods.
"""
        return prompt
    
    def _determine_go_module(self, filename: str) -> str:
        """
        Determine Go module/package from Python filename
        
        Args:
            filename: Python filename
            
        Returns:
            Go module name
        """
        name_lower = filename.lower()
        
        if 'invoice' in name_lower:
            return 'invoice'
        elif 'ledger' in name_lower or 'journal' in name_lower:
            return 'ledger'
        elif 'tax' in name_lower:
            return 'tax'
        elif 'party' in name_lower:
            return 'party'
        elif 'payment' in name_lower:
            return 'payment'
        else:
            return 'common'
    
    def _write_conversion_report(self, converted_modules: List[Dict[str, Any]], context: Dict[str, Any]):
        """Write conversion report"""
        with open(self.conversion_report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("PYTHON TO GO CONVERSION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write("SUMMARY:\n")
            f.write(f"  Total Modules Converted: {len(converted_modules)}\n")
            f.write(f"  Warnings: {len(self.conversion_warnings)}\n")
            f.write(f"  Business Domains: {', '.join(context.get('business_domains', []))}\n")
            f.write("\n" + "-"*80 + "\n\n")
            
            f.write("CONVERTED MODULES:\n\n")
            for module in converted_modules:
                f.write(f"Python: {module['python_file']}\n")
                f.write(f"Go:     {module['go_file']}\n")
                f.write(f"Module: {module['module']}\n")
                f.write("\n")
            
            if self.conversion_warnings:
                f.write("\n" + "-"*80 + "\n\n")
                f.write("WARNINGS & ISSUES:\n\n")
                for warning in self.conversion_warnings:
                    f.write(f"File: {warning['file']}\n")
                    f.write(f"Issue: {warning.get('error', 'Unknown error')}\n")
                    if 'fallback' in warning:
                        f.write(f"Action: Used {warning['fallback']} conversion\n")
                    f.write("\n")
            
            f.write("\n" + "="*80 + "\n\n")
            f.write("NEXT STEPS:\n")
            f.write("1. Review generated Go code in modern/ directory\n")
            f.write("2. Verify accounting business logic is preserved\n")
            f.write("3. Run tests: pytest tests/\n")
            f.write("4. Address any TODO comments in Go code\n")
            f.write("5. Validate with QA scripts\n")
