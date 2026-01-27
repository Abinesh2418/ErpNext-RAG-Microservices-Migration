"""
AI Converter
Converts Python Accounts code to Go using Groq API (llama-3.3-70b-versatile)
Supports parallel conversion with Redis caching and Qdrant semantic context
"""

import os
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Redis and Qdrant integrations
from ..redis import RedisStore
from ..qdrant import QdrantIndex
from ..utils.file_chunker import FileChunker


class AIConverter:
    """AI-powered Python to Go converter with Groq API and caching"""
    
    def __init__(self, config, logger):
        """
        Initialize AI converter
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.conversion_report_file = None
        self.conversion_warnings = []
        
        # Groq API Configuration
        self.api_key = os.getenv('GROQ_API_KEY')
        self.model = os.getenv('GROQ_MODEL')
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.2'))
        self.primary_workers = int(os.getenv('PRIMARY_WORKERS', '4'))
        
        # Groq API endpoint
        self.api_base_url = "https://api.groq.com/openai/v1"
        self.chat_endpoint = f"{self.api_base_url}/chat/completions"
        
        # Initialize Redis store for caching
        self.redis_store = RedisStore(config, logger)
        
        # Initialize Qdrant index for semantic search
        self.qdrant_index = QdrantIndex(config, logger)
        
        # Initialize file chunker
        self.chunker = FileChunker(logger, max_chunk_lines=500)
        
        # Cloud API is always available (no local dependency check needed)
        self.ollama_available = True
        
        self.logger.info(f"AIConverter initialized with Groq API")
        self.logger.info(f"Model: {self.model} ({self.primary_workers} workers)")
    
    def convert(self, context: Dict[str, Any], files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert Python files to Go (incremental, file-by-file with caching)
        
        Args:
            context: Prepared context from dependency analyzer
            files: List of file information from scanner
            
        Returns:
            Conversion results dictionary
        """
        from ..utils.logger import get_timestamped_filename
        
        self.logger.info(f"Starting incremental AI conversion for {len(files)} files")
        
        # Create results directory
        results_dir = self.config.get('RESULTS_DIR')
        self.conversion_report_file = results_dir / get_timestamped_filename('conversion_report', 'txt')
        
        modern_dir = self.config.get('MODERN_DIR')
        
        converted_modules = []
        cache_hits = 0
        cache_misses = 0
        skipped_conversions = 0
        total_conversion_time = 0
        
        # Convert each file one-by-one
        for file_info in files:
            if not file_info.get('valid_syntax', False):
                self.logger.warning(f"Skipping invalid file: {file_info['name']}")
                continue
            
            try:
                file_path = file_info['path']
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if file changed using Redis
                if self.redis_store.is_available():
                    file_changed = self.redis_store.file_changed(file_path, content)
                    
                    if not file_changed:
                        # Try to use cached conversion
                        start_time = time.time()
                        cached = self.redis_store.get_conversion_output(file_path)
                        if cached:
                            go_code = cached['go_code']
                            metadata = cached.get('metadata', {})
                            cache_hits += 1
                            skipped_conversions += 1
                            elapsed_time = time.time() - start_time
                            total_conversion_time += elapsed_time
                            self.logger.info(f"✓ Cache HIT: Reusing conversion for {file_info['name']} (⏱️  {elapsed_time:.2f}s)")
                            
                            # Write cached Go code
                            go_module = self._determine_go_module(file_info['name'])
                            go_dir = modern_dir / go_module
                            go_dir.mkdir(parents=True, exist_ok=True)
                            go_file = go_dir / f"{Path(file_info['name']).stem}.go"
                            with open(go_file, 'w', encoding='utf-8') as f:
                                f.write(go_code)
                            
                            converted_modules.append({
                                'python_file': file_info['name'],
                                'go_file': str(go_file),
                                'module': go_module,
                                'cached': True,
                                'conversion_time': elapsed_time
                            })
                            continue
                
                # Cache miss or file changed - convert
                cache_misses += 1
                self.logger.info(f"⚡ Cache MISS: Converting {file_info['name']}...")
                start_time = time.time()
                go_code = self._convert_file(file_info, context)
                elapsed_time = time.time() - start_time
                total_conversion_time += elapsed_time
                
                if go_code:
                    # Determine Go module structure
                    go_module = self._determine_go_module(file_info['name'])
                    go_dir = modern_dir / go_module
                    go_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Write Go file
                    go_file = go_dir / f"{Path(file_info['name']).stem}.go"
                    with open(go_file, 'w', encoding='utf-8') as f:
                        f.write(go_code)
                    
                    # Cache conversion output in Redis
                    if self.redis_store.is_available():
                        self.redis_store.store_conversion_output(
                            file_path, go_code, {'module': go_module}
                        )
                    
                    converted_modules.append({
                        'python_file': file_info['name'],
                        'go_file': str(go_file),
                        'module': go_module,
                        'cached': False,
                        'conversion_time': elapsed_time
                    })
                    
                    self.logger.info(f"✓ Converted: {file_info['name']} → {go_file.name} (⏱️  {elapsed_time:.2f}s)")
                    
            except Exception as e:
                self.logger.error(f"Failed to convert {file_info['name']}: {e}")
                self.conversion_warnings.append({
                    'file': file_info['name'],
                    'error': str(e)
                })
        
        # Write conversion report
        self._write_conversion_report(converted_modules, context, cache_hits, cache_misses, skipped_conversions, total_conversion_time)
        
        # Log timing summary
        avg_time = total_conversion_time / len(converted_modules) if converted_modules else 0
        self.logger.info(f"\n⏱️  TIMING SUMMARY:")
        self.logger.info(f"   Total Conversion Time: {total_conversion_time:.2f}s")
        self.logger.info(f"   Average per File: {avg_time:.2f}s")
        self.logger.info(f"   Files Processed: {len(converted_modules)}")
        
        result = {
            'modules_created': len(converted_modules),
            'warnings': len(self.conversion_warnings),
            'converted_modules': converted_modules,
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'skipped_conversions': skipped_conversions,
            'total_conversion_time': total_conversion_time,
            'average_conversion_time': avg_time,
            'report_file': str(self.conversion_report_file),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(
            f"Conversion complete: {len(converted_modules)} modules created "
            f"(Cache: {cache_hits} hits, {cache_misses} misses, {skipped_conversions} skipped)"
        )
        return result
    
    def _convert_file(self, file_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Convert single Python file to Go (with chunking for large files)
        
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
        
        # Check if file needs chunking (>500 lines)
        if self.chunker.should_chunk_file(file_info):
            self.logger.info(f"📄 Large file detected ({file_info.get('lines', 0)} lines), using chunking...")
            return self._convert_with_chunks(python_code, file_info, context)
        
        # If AI is available, use it
        if self.ollama_available:
            return self._ai_convert(python_code, file_info, context)
        else:
            return self._template_convert(python_code, file_info)
    
    def _ai_convert(self, python_code: str, file_info: Dict[str, Any], context: Dict[str, Any], use_streaming: bool = True) -> str:
        """
        Convert using AI (Ollama) with optional streaming and early stop
        
        Args:
            python_code: Python source code
            file_info: File information
            context: Context information
            use_streaming: Enable streaming API with early stop (default: True)
            
        Returns:
            Go code as string
        """
        try:
            # Build conversion prompt with Qdrant context
            prompt = self._build_conversion_prompt(python_code, file_info, context)
            
            # Select model (smart model for complex files)
            lines = file_info.get('lines', 0)
            use_smart_model = lines >= 200
            model = self._select_model(use_smart_model)
            
            # Use streaming API for faster response and early stop
            if use_streaming:
                return self._ai_convert_streaming(prompt, model, file_info, use_smart_model)
            else:
                return self._ai_convert_non_streaming(prompt, model, file_info, python_code, use_smart_model)
            
        except Exception as e:
            self.logger.error(f"AI conversion failed: {e}")
            self.conversion_warnings.append({
                'file': file_info['name'],
                'error': f"AI conversion failed: {str(e)}",
                'fallback': 'template'
            })
            return self._template_convert(python_code if 'python_code' in locals() else "", file_info)
    
    def _ai_convert_streaming(self, prompt: str, model: str, file_info: Dict[str, Any], use_smart_model: bool, retry_count: int = 0) -> str:
        """
        Convert using Cloud API streaming with early stop detection
        
        Args:
            prompt: Conversion prompt
            model: Model name
            file_info: File information
            use_smart_model: Whether using smart model
            retry_count: Number of retries attempted (for fallback)
            
        Returns:
            Go code as string
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert in converting Python accounting/ERP code to Go. "
                                   "Preserve business logic, accounting rules, and data integrity. "
                                   "Generate idiomatic Go code with proper error handling. "
                                   "CRITICAL: Implement FULL business logic. DO NOT use TODO comments. "
                                   "Output ONLY Go code without explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": 4096,
                "stream": True
            }
            
            # Call Cloud API streaming (5-minute timeout for large files)
            response = requests.post(
                self.chat_endpoint,
                headers=headers,
                json=data,
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            # Collect streaming response with early stop detection
            full_response = []
            in_code_block = False
            brace_count = 0
            last_significant_line = ""
            tokens_since_last_code = 0
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                
                                if content:
                                    full_response.append(content)
                                    
                                    # Track if we're in a code block
                                    if "```go" in content:
                                        in_code_block = True
                                    elif "```" in content and in_code_block:
                                        self.logger.debug("Code block end detected, stopping generation")
                                        break
                                    
                                    # Track brace count to detect code completion
                                    brace_count += content.count('{') - content.count('}')
                                    
                                    # Check if we have a complete Go file
                                    if in_code_block or ('package ' in ''.join(full_response[:10])):
                                        for char in content:
                                            if char == '\n':
                                                line = last_significant_line.strip()
                                                if line and not line.startswith('//'):
                                                    tokens_since_last_code = 0
                                                else:
                                                    tokens_since_last_code += 1
                                                last_significant_line = ""
                                            else:
                                                last_significant_line += char
                                        
                                        # Early stop: balanced braces + trailing content
                                        if brace_count == 0 and len(full_response) > 20:
                                            if tokens_since_last_code > 5:
                                                self.logger.debug("Code completion detected, stopping")
                                                break
                        except json.JSONDecodeError:
                            continue
            
            go_code = ''.join(full_response)
            
            # Extract Go code from markdown if present
            if "```go" in go_code:
                go_code = go_code.split("```go")[1].split("```")[0].strip()
            elif "```" in go_code:
                parts = go_code.split("```")
                if len(parts) >= 2:
                    go_code = parts[1].strip()
            
            # Remove trailing explanations/comments after the last closing brace
            lines = go_code.splitlines()
            last_code_line = len(lines) - 1
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if line and not line.startswith('//') and not line.startswith('/*'):
                    last_code_line = i
                    break
            
            go_code = '\n'.join(lines[:last_code_line + 1])
            
            return go_code
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for memory error and retry
            if "system memory" in error_msg.lower() or "memory" in error_msg.lower():
                self.logger.warning(f"Memory error with {model}: {error_msg}")
                self.logger.error(f"Memory constraints - cannot retry with Groq")
                raise Exception(f"Insufficient memory for conversion. Model: {model}. Error: {error_msg}")
            
            self.logger.error(f"Streaming conversion failed: {e}")
            # For non-memory errors, fallback to non-streaming
            return self._ai_convert_non_streaming(prompt, model, file_info, "", use_smart_model)
    
    def _ai_convert_non_streaming(self, prompt: str, model: str, file_info: Dict[str, Any], python_code: str, use_smart_model: bool, retry_count: int = 0) -> str:
        """
        Convert using Cloud API non-streaming
        
        Args:
            prompt: Conversion prompt
            model: Model name
            file_info: File information
            python_code: Original Python code
            use_smart_model: Whether using smart model
            retry_count: Number of retries attempted (for fallback)
            
        Returns:
            Go code as string
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert in converting Python accounting/ERP code to Go. "
                                   "Preserve business logic, accounting rules, and data integrity. "
                                   "Generate idiomatic Go code with proper error handling. "
                                   "CRITICAL: Implement FULL business logic. DO NOT use TODO comments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": 4096,
                "stream": False
            }
            
            # 5-minute timeout for large file conversions
            response = requests.post(
                self.chat_endpoint,
                headers=headers,
                json=data,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract content from OpenAI-format response
            if 'choices' in result and len(result['choices']) > 0:
                go_code = result['choices'][0]['message']['content']
            else:
                raise Exception("Invalid API response format")
            
            # Extract Go code from markdown if present
            if "```go" in go_code:
                go_code = go_code.split("```go")[1].split("```")[0].strip()
            elif "```" in go_code:
                go_code = go_code.split("```")[1].split("```")[0].strip()
            
            return go_code
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for memory error - try fallback model
            if "system memory" in error_msg.lower() or "requires more" in error_msg.lower():
                self.logger.warning(f"⚠️ Memory error with {model}: {error_msg}")
                self.logger.error("❌ Memory constraints - cannot retry with Groq")
                raise Exception(f"Insufficient memory for conversion. Model: {model}. Error: {error_msg}")
            
            self.logger.error(f"AI conversion failed: {e}")
            self.conversion_warnings.append({
                'file': file_info['name'],
                'error': f"AI conversion failed: {str(e)}",
                'fallback': 'template'
            })
            return self._template_convert(python_code, file_info)
    
    def _convert_with_chunks(self, python_code: str, file_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Convert large file using chunking strategy
        
        Args:
            python_code: Python source code
            file_info: File information
            context: Context information
            
        Returns:
            Complete Go code reassembled from chunks
        """
        try:
            # Split file into semantic chunks
            chunks = self.chunker.chunk_file(file_info['path'], python_code)
            
            if not chunks:
                self.logger.warning(f"Chunking failed for {file_info['name']}, using standard conversion")
                return self._ai_convert(python_code, file_info, context, use_streaming=False)
            
            self.logger.info(f"Converting {len(chunks)} chunks for {file_info['name']}")
            
            # Convert each chunk
            chunk_results = []
            for i, chunk in enumerate(chunks):
                self.logger.info(f"  Converting chunk {i+1}/{len(chunks)}: {chunk.name}")
                
                # Build prompt for this chunk with context
                chunk_prompt = self._build_chunk_prompt(chunk, file_info, context)
                
                # Select model based on chunk complexity
                use_smart = len(chunk.code.splitlines()) >= 100
                model = self._select_model(use_smart)
                
                # Convert chunk with streaming
                try:
                    go_code = self._ai_convert_streaming(chunk_prompt, model, file_info, use_smart)
                    chunk_results.append({
                        'chunk_id': chunk.chunk_id,
                        'go_code': go_code,
                        'name': chunk.name
                    })
                except Exception as e:
                    self.logger.error(f"Failed to convert chunk {i+1}: {e}")
                    # Use template for failed chunk
                    chunk_results.append({
                        'chunk_id': chunk.chunk_id,
                        'go_code': f"// TODO: Chunk conversion failed for {chunk.name}\n",
                        'name': chunk.name
                    })
            
            # Reassemble chunks into complete Go file
            complete_go_code = self.chunker.reassemble_chunks(chunk_results)
            
            self.logger.info(f"✓ Reassembled {len(chunks)} chunks into complete Go file")
            return complete_go_code
            
        except Exception as e:
            self.logger.error(f"Chunked conversion failed: {e}")
            # Fallback to standard conversion
            return self._ai_convert(python_code, file_info, context, use_streaming=False)
    
    def _build_chunk_prompt(self, chunk, file_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Build conversion prompt for a specific chunk
        
        Args:
            chunk: CodeChunk object
            file_info: File information
            context: Context information
            
        Returns:
            Prompt string
        """
        prompt = f"""Convert this Python code chunk to Go.

**Context (Module-level imports and setup):**
```python
{chunk.context}
```

**Chunk to Convert ({chunk.chunk_type}: {chunk.name}):**
```python
{chunk.code}
```

**Instructions:**
- This is chunk {chunk.chunk_id + 1} from file: {file_info['name']}
- Preserve the business logic exactly
- Use proper Go idioms and error handling
- DO NOT include package declaration or imports (they will be added during reassembly)
- Output ONLY the converted Go code for this specific chunk
- CRITICAL: No TODO comments - implement full logic

Generate the Go code:"""
        
        return prompt
    
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
        """
        Build prompt for AI conversion with Qdrant semantic context
        
        Args:
            python_code: Python source code
            file_info: File information
            context: Dependency context
            
        Returns:
            Enhanced prompt with semantic context
        """
        # Get relevant semantic context from Qdrant
        semantic_context = []
        if self.qdrant_index.is_available():
            file_path = file_info.get('path', file_info['name'])
            relevant_items = self.qdrant_index.get_file_context(file_path, top_k=10)  # Increased from 3 to 10
            
            for item in relevant_items:
                if item['type'] == 'file':
                    semantic_context.append(f"Related file: {item['meaning']}")
                elif item['type'] == 'function':
                    semantic_context.append(f"Related function: {item['function_name']} - {item['meaning']}")
                elif item['type'] == 'dependency':
                    semantic_context.append(f"Dependency: {item['meaning']}")
        
        # Build semantic context section
        semantic_section = ""
        if semantic_context:
            semantic_section = "\n\nRelevant Context from Codebase:\n" + "\n".join(f"- {ctx}" for ctx in semantic_context)
        
        # Get dependency summaries
        dep_summary = context.get('dependency_summary', '')
        if dep_summary:
            dep_section = f"\n\nDependency Information:\n{dep_summary}"
        else:
            dep_section = ""
        
        prompt = f"""Convert the following Python ERPNext Accounts code to idiomatic Go.

Context:
- Accounting/ERP system module
- Business domains: {', '.join(context.get('business_domains', []))}
- File: {file_info['name']}{semantic_section}{dep_section}

Requirements:
1. Preserve ALL business logic exactly - no simplifications
2. Implement complete functionality - NO TODO comments
3. Use database/sql for database operations
4. Include comprehensive error handling
5. Add comments explaining accounting logic
6. Use Go idioms: interfaces, error returns, struct composition

Python Code:
```python
{python_code}
```

Generate production-ready Go code with complete implementations.
Include package declaration, imports, structs, and fully implemented functions.
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
    
    def _write_conversion_report(self, converted_modules: List[Dict[str, Any]], context: Dict[str, Any], 
                                 cache_hits: int = 0, cache_misses: int = 0, skipped_conversions: int = 0, total_time: float = 0):
        """Write conversion report with cache statistics and timing"""
        with open(self.conversion_report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("PYTHON TO GO CONVERSION REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Calculate timing stats
            avg_time = total_time / len(converted_modules) if converted_modules else 0
            cached_modules = [m for m in converted_modules if m.get('cached', False)]
            uncached_modules = [m for m in converted_modules if not m.get('cached', False)]
            
            avg_cached_time = sum(m.get('conversion_time', 0) for m in cached_modules) / len(cached_modules) if cached_modules else 0
            avg_uncached_time = sum(m.get('conversion_time', 0) for m in uncached_modules) / len(uncached_modules) if uncached_modules else 0
            
            f.write("SUMMARY:\n")
            f.write(f"  Total Modules Converted: {len(converted_modules)}\n")
            f.write(f"  Cache Hits: {cache_hits}\n")
            f.write(f"  Cache Misses: {cache_misses}\n")
            f.write(f"  Skipped Conversions: {skipped_conversions}\n")
            cache_efficiency = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0
            f.write(f"  Cache Efficiency: {cache_efficiency:.1f}%\n")
            f.write(f"  Warnings: {len(self.conversion_warnings)}\n")
            f.write(f"  Business Domains: {', '.join(context.get('business_domains', []))}\n")
            f.write(f"\n")
            f.write(f"TIMING:\n")
            f.write(f"  Total Time: {total_time:.2f}s\n")
            f.write(f"  Average per File: {avg_time:.2f}s\n")
            if cached_modules:
                f.write(f"  Average (Cached): {avg_cached_time:.3f}s\n")
            if uncached_modules:
                f.write(f"  Average (Fresh Conversion): {avg_uncached_time:.2f}s\n")
            f.write("\n" + "-"*80 + "\n\n")
            
            f.write("CONVERTED MODULES:\n\n")
            for module in converted_modules:
                cached_flag = " [CACHED]" if module.get('cached', False) else ""
                conversion_time = module.get('conversion_time', 0)
                f.write(f"Python: {module['python_file']}{cached_flag}\n")
                f.write(f"Go:     {module['go_file']}\n")
                f.write(f"Module: {module['module']}\n")
                f.write(f"Time:   {conversion_time:.2f}s\n")
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
            f.write("\n")
            f.write("CACHING NOTES:\n")
            f.write(f"- Redis caching is {'enabled' if self.redis_store.is_available() else 'disabled'}\n")
            f.write(f"- Qdrant semantic indexing is {'enabled' if self.qdrant_index.is_available() else 'disabled'}\n")
            f.write("- Files are re-converted only when source changes detected\n")
    
    def _select_model(self, use_smart_model: bool = False) -> str:
        """
        Select LLM model (Groq API uses single model)
        
        Args:
            use_smart_model: Ignored, kept for compatibility
            
        Returns:
            Model name string
        """
        return self.model
    
    def _convert_file_with_model(
        self,
        file_info: Dict[str, Any],
        context: Dict[str, Any],
        use_fast_model: bool = True
    ) -> Optional[str]:
        """
        Convert file with specified model (used by worker pool)
        
        Args:
            file_info: File information dictionary
            context: Context information
            use_fast_model: True for fast model, False for smart model
            
        Returns:
            Go code as string, or None on failure
        """
        file_path = Path(file_info['path'])
        
        # Read Python code
        with open(file_path, 'r', encoding='utf-8') as f:
            python_code = f.read()
        
        try:
            prompt = self._build_conversion_prompt(python_code, file_info, context)
            model = self._select_model(not use_fast_model)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert in converting Python accounting/ERP code to Go. "
                                   "Preserve business logic, accounting rules, and data integrity. "
                                   "Generate idiomatic Go code with proper error handling. "
                                   "CRITICAL: Implement FULL business logic. DO NOT use TODO comments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": 4096,
                "stream": False
            }
            
            # 5-minute timeout for worker pool conversions
            response = requests.post(
                self.chat_endpoint,
                headers=headers,
                json=data,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract content from OpenAI-format response
            if 'choices' in result and len(result['choices']) > 0:
                go_code = result['choices'][0]['message']['content']
            else:
                raise Exception("Invalid API response format")
            
            # Extract Go code from markdown
            if "```go" in go_code:
                go_code = go_code.split("```go")[1].split("```")[0].strip()
            elif "```" in go_code:
                go_code = go_code.split("```")[1].split("```")[0].strip()
            
            return go_code
            
        except Exception as e:
            self.logger.error(f"Conversion failed for {file_info['name']}: {e}")
            return None
    
    def convert_parallel(
        self,
        context: Dict[str, Any],
        files: List[Dict[str, Any]],
        dependency_levels: List[List[str]],
        num_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Convert files in parallel using dependency-aware scheduling
        
        Args:
            context: Prepared context from dependency analyzer
            files: List of file information from scanner
            dependency_levels: List of dependency levels (files grouped by level)
            num_workers: Number of parallel workers
            
        Returns:
            Conversion results dictionary
        """
        from ..utils.logger import get_timestamped_filename
        from ..utils.worker_pool import WorkerPool, WorkItem
        
        self.logger.info(
            f"🚀 Starting PARALLEL conversion: {len(files)} files, "
            f"{len(dependency_levels)} levels, {num_workers} workers"
        )
        
        # Create results directory
        results_dir = self.config.get('RESULTS_DIR')
        self.conversion_report_file = results_dir / get_timestamped_filename('conversion_report', 'txt')
        modern_dir = self.config.get('MODERN_DIR')
        
        # Create worker pool
        pool = WorkerPool(self, self.logger, num_workers)
        
        # Track conversion stats
        converted_modules = []
        cache_hits = 0
        cache_misses = 0
        total_conversion_time = time.time()
        
        # Build file path to info mapping (with multiple lookup keys)
        file_map = {}
        for f in files:
            # Add by full path
            file_map[f['path']] = f
            # Add by file name
            file_map[f['name']] = f
            # Add by stem (name without extension)
            file_map[Path(f['name']).stem] = f
        
        self.logger.info(f"📂 File map created with {len(files)} files")
        self.logger.debug(f"   Mapped keys: {list(file_map.keys())[:10]}...")  # Show first 10
        
        # Process each dependency level
        for level_idx, level_files in enumerate(dependency_levels):
            self.logger.info(f"\n📊 Processing Level {level_idx}: {len(level_files)} files (parallel)")
            self.logger.debug(f"   Level {level_idx} file identifiers: {level_files[:5]}...")  # Show first 5
            
            # Create work items for this level
            work_items = []
            for file_identifier in level_files:
                # Try multiple ways to find the file
                file_info = None
                
                # Try direct lookup
                if file_identifier in file_map:
                    file_info = file_map[file_identifier]
                # Try as Path object
                elif str(Path(file_identifier)) in file_map:
                    file_info = file_map[str(Path(file_identifier))]
                # Try just the filename
                elif Path(file_identifier).name in file_map:
                    file_info = file_map[Path(file_identifier).name]
                # Try the stem
                elif Path(file_identifier).stem in file_map:
                    file_info = file_map[Path(file_identifier).stem]
                
                if file_info:
                    # Determine if file is simple (use fast model)
                    lines = file_info.get('lines', 0)
                    use_fast = lines < 200
                    
                    work_item = WorkItem(
                        file_info=file_info,
                        context=context,
                        level=level_idx,
                        use_fast_model=use_fast
                    )
                    work_items.append(work_item)
                else:
                    self.logger.warning(f"⚠️  Could not find file info for: {file_identifier}")
            
            self.logger.info(f"   Created {len(work_items)} work items for level {level_idx}")
            
            if not work_items:
                continue
            
            # Submit work for this level
            pool.submit_work(work_items)
            
            # Wait for level completion
            results = pool.wait_for_completion(len(work_items))
            
            # Process results
            for result in results:
                self.logger.info(f"📝 Processing result: {result.file_path}, success={result.success}, cached={result.cached}")
                
                if result.cached:
                    cache_hits += 1
                else:
                    cache_misses += 1
                
                if result.success and result.go_code:
                    # Write Go file
                    file_name = Path(result.file_path).stem
                    
                    # Find file info with flexible lookup
                    file_info = None
                    for key in [result.file_path, Path(result.file_path).name, file_name]:
                        if key in file_map:
                            file_info = file_map[key]
                            break
                    
                    if not file_info:
                        self.logger.warning(f"⚠️  No file info found for {result.file_path}, using defaults")
                        file_info = {'name': Path(result.file_path).name}
                    
                    go_module = self._determine_go_module(Path(result.file_path).name)
                    go_dir = modern_dir / go_module
                    go_dir.mkdir(parents=True, exist_ok=True)
                    go_file = go_dir / f"{file_name}.go"
                    
                    self.logger.info(f"✍️  Writing Go file: {go_file}")
                    
                    with open(go_file, 'w', encoding='utf-8') as f:
                        f.write(result.go_code)
                    
                    self.logger.info(f"✅ Successfully wrote: {go_file}")
                    
                    converted_modules.append({
                        'python_file': Path(result.file_path).name,
                        'go_file': str(go_file),
                        'module': go_module,
                        'cached': result.cached,
                        'conversion_time': result.elapsed_time,
                        'model_used': result.model_used,
                        'level': level_idx
                    })
        
        # Shutdown pool
        pool.shutdown()
        
        total_conversion_time = time.time() - total_conversion_time
        avg_time = total_conversion_time / len(converted_modules) if converted_modules else 0
        
        # Write report
        self._write_conversion_report(
            converted_modules,
            context,
            cache_hits,
            cache_misses,
            0,
            total_conversion_time
        )
        
        # Log summary
        self.logger.info(f"\n⏱️  PARALLEL CONVERSION COMPLETE:")
        self.logger.info(f"   Total Time: {total_conversion_time:.2f}s")
        self.logger.info(f"   Files Converted: {len(converted_modules)}")
        self.logger.info(f"   Average per File: {avg_time:.2f}s")
        self.logger.info(f"   Cache Hits: {cache_hits}")
        self.logger.info(f"   Cache Misses: {cache_misses}")
        self.logger.info(f"   Throughput: {len(converted_modules)/total_conversion_time:.2f} files/second")
        
        return {
            'modules_created': len(converted_modules),
            'warnings': len(self.conversion_warnings),
            'converted_modules': converted_modules,
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'total_conversion_time': total_conversion_time,
            'average_conversion_time': avg_time,
            'report_file': str(self.conversion_report_file),
            'timestamp': datetime.now().isoformat(),
            'parallel_execution': True,
            'num_workers': num_workers,
            'dependency_levels': len(dependency_levels)
        }
