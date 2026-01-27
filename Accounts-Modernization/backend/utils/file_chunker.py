"""
File Chunker
Splits large Python files into semantic chunks for efficient conversion
Preserves imports, docstrings, and context for each chunk
"""

import ast
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Represents a chunk of code to be converted"""
    chunk_id: int
    start_line: int
    end_line: int
    code: str
    chunk_type: str  # 'imports', 'function', 'class', 'other'
    name: str  # Name of function/class or 'module_setup'
    dependencies: List[str]  # Names of other chunks this depends on
    context: str  # Shared context (imports, module docstring)


class FileChunker:
    """Splits large Python files into manageable chunks"""
    
    def __init__(self, logger, max_chunk_lines: int = 500):
        """
        Initialize file chunker
        
        Args:
            logger: Logger instance
            max_chunk_lines: Maximum lines per chunk (default: 500)
        """
        self.logger = logger
        self.max_chunk_lines = max_chunk_lines
    
    def should_chunk_file(self, file_info: Dict[str, Any]) -> bool:
        """
        Determine if a file needs chunking
        
        Args:
            file_info: File information dictionary
            
        Returns:
            True if file exceeds max_chunk_lines
        """
        lines = file_info.get('lines', 0)
        return lines > self.max_chunk_lines
    
    def chunk_file(self, file_path: str, code: str) -> List[CodeChunk]:
        """
        Split a large file into semantic chunks
        
        Args:
            file_path: Path to the file
            code: Python source code
            
        Returns:
            List of CodeChunk objects
        """
        self.logger.info(f"📄 Chunking file: {file_path}")
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}")
            return []
        
        lines = code.splitlines(keepends=True)
        chunks = []
        chunk_id = 0
        
        # Extract module-level imports and docstring (shared context)
        module_context = self._extract_module_context(tree, lines)
        
        # Extract top-level definitions
        definitions = self._extract_definitions(tree, lines)
        
        # Group definitions into chunks
        current_chunk_defs = []
        current_chunk_lines = 0
        
        for defn in definitions:
            defn_lines = defn['end_line'] - defn['start_line'] + 1
            
            # If this definition alone exceeds max, split it further
            if defn_lines > self.max_chunk_lines:
                # Flush current chunk if any
                if current_chunk_defs:
                    chunks.append(self._create_chunk(
                        chunk_id, current_chunk_defs, lines, module_context
                    ))
                    chunk_id += 1
                    current_chunk_defs = []
                    current_chunk_lines = 0
                
                # Split large definition (e.g., large class)
                sub_chunks = self._split_large_definition(
                    defn, lines, module_context, chunk_id
                )
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
            
            # If adding this would exceed max, flush current chunk
            elif current_chunk_lines + defn_lines > self.max_chunk_lines and current_chunk_defs:
                chunks.append(self._create_chunk(
                    chunk_id, current_chunk_defs, lines, module_context
                ))
                chunk_id += 1
                current_chunk_defs = [defn]
                current_chunk_lines = defn_lines
            
            # Add to current chunk
            else:
                current_chunk_defs.append(defn)
                current_chunk_lines += defn_lines
        
        # Flush remaining definitions
        if current_chunk_defs:
            chunks.append(self._create_chunk(
                chunk_id, current_chunk_defs, lines, module_context
            ))
        
        self.logger.info(f"✓ Created {len(chunks)} chunks for {file_path}")
        return chunks
    
    def _extract_module_context(self, tree: ast.AST, lines: List[str]) -> str:
        """
        Extract module-level imports and docstring
        
        Args:
            tree: AST tree
            lines: Source code lines
            
        Returns:
            Module context string
        """
        context_parts = []
        
        # Module docstring
        docstring = ast.get_docstring(tree)
        if docstring:
            context_parts.append(f'"""\n{docstring}\n"""')
        
        # All imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                start = node.lineno - 1
                context_parts.append(''.join(lines[start:node.end_lineno]))
            elif isinstance(node, ast.ImportFrom):
                start = node.lineno - 1
                context_parts.append(''.join(lines[start:node.end_lineno]))
        
        return '\n'.join(context_parts)
    
    def _extract_definitions(self, tree: ast.AST, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Extract top-level function and class definitions
        
        Args:
            tree: AST tree
            lines: Source code lines
            
        Returns:
            List of definition dictionaries
        """
        definitions = []
        
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defn = {
                    'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                    'name': node.name,
                    'start_line': node.lineno,
                    'end_line': node.end_lineno,
                    'node': node
                }
                definitions.append(defn)
        
        return definitions
    
    def _create_chunk(
        self, 
        chunk_id: int, 
        definitions: List[Dict[str, Any]], 
        lines: List[str],
        context: str
    ) -> CodeChunk:
        """
        Create a CodeChunk from definitions
        
        Args:
            chunk_id: Chunk identifier
            definitions: List of definition dictionaries
            lines: Source code lines
            context: Module context (imports, docstrings)
            
        Returns:
            CodeChunk object
        """
        start_line = min(d['start_line'] for d in definitions)
        end_line = max(d['end_line'] for d in definitions)
        
        # Extract code for this chunk
        chunk_lines = lines[start_line - 1:end_line]
        code = ''.join(chunk_lines)
        
        # Determine chunk type
        if len(definitions) == 1:
            chunk_type = definitions[0]['type']
            name = definitions[0]['name']
        else:
            chunk_type = 'multiple'
            names = [d['name'] for d in definitions]
            name = ', '.join(names[:3]) + ('...' if len(names) > 3 else '')
        
        # Extract dependencies (simplified - just function/class names referenced)
        dependencies = []
        for defn in definitions:
            for node in ast.walk(defn['node']):
                if isinstance(node, ast.Name):
                    dependencies.append(node.id)
        
        return CodeChunk(
            chunk_id=chunk_id,
            start_line=start_line,
            end_line=end_line,
            code=code,
            chunk_type=chunk_type,
            name=name,
            dependencies=list(set(dependencies)),
            context=context
        )
    
    def _split_large_definition(
        self,
        defn: Dict[str, Any],
        lines: List[str],
        context: str,
        start_chunk_id: int
    ) -> List[CodeChunk]:
        """
        Split a large class or function into smaller chunks
        
        Args:
            defn: Definition dictionary
            lines: Source code lines
            context: Module context
            start_chunk_id: Starting chunk ID
            
        Returns:
            List of CodeChunks
        """
        chunks = []
        
        if defn['type'] == 'class':
            # Split class by methods
            methods = []
            for node in defn['node'].body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        'type': 'method',
                        'name': node.name,
                        'start_line': node.lineno,
                        'end_line': node.end_lineno,
                        'node': node
                    })
            
            # Group methods into chunks
            if methods:
                current_methods = []
                current_lines = 0
                chunk_id = start_chunk_id
                
                # Add class header to context
                class_header_end = methods[0]['start_line'] - 1
                class_header = ''.join(lines[defn['start_line'] - 1:class_header_end])
                enhanced_context = f"{context}\n\n{class_header}"
                
                for method in methods:
                    method_lines = method['end_line'] - method['start_line'] + 1
                    
                    if current_lines + method_lines > self.max_chunk_lines and current_methods:
                        chunks.append(self._create_chunk(
                            chunk_id, current_methods, lines, enhanced_context
                        ))
                        chunk_id += 1
                        current_methods = [method]
                        current_lines = method_lines
                    else:
                        current_methods.append(method)
                        current_lines += method_lines
                
                if current_methods:
                    chunks.append(self._create_chunk(
                        chunk_id, current_methods, lines, enhanced_context
                    ))
        else:
            # For large functions, just create a single chunk
            # (splitting functions is complex and rarely needed)
            code = ''.join(lines[defn['start_line'] - 1:defn['end_line']])
            chunks.append(CodeChunk(
                chunk_id=start_chunk_id,
                start_line=defn['start_line'],
                end_line=defn['end_line'],
                code=code,
                chunk_type=defn['type'],
                name=defn['name'],
                dependencies=[],
                context=context
            ))
        
        return chunks
    
    def reassemble_chunks(self, chunk_results: List[Dict[str, Any]]) -> str:
        """
        Reassemble converted chunks into a complete Go file
        
        Args:
            chunk_results: List of conversion results for each chunk
            
        Returns:
            Complete Go source code
        """
        if not chunk_results:
            return ""
        
        # Start with package declaration and imports (from first chunk)
        parts = []
        
        # Extract package declaration from first chunk
        first_go_code = chunk_results[0].get('go_code', '')
        package_lines = []
        import_lines = []
        
        for line in first_go_code.splitlines():
            if line.startswith('package '):
                package_lines.append(line)
            elif line.startswith('import ') or line.strip().startswith('"'):
                import_lines.append(line)
            elif not line.strip() or line.strip().startswith('//'):
                continue  # Skip empty lines and comments in header
            else:
                break  # Stop at first code line
        
        # Add package and imports
        if package_lines:
            parts.append('\n'.join(package_lines))
            parts.append('')
        
        if import_lines:
            parts.append('\n'.join(import_lines))
            parts.append('')
        
        # Add converted code from all chunks (without redundant package/imports)
        for result in chunk_results:
            go_code = result.get('go_code', '')
            
            # Skip package declaration and imports in subsequent chunks
            code_lines = []
            skip_header = True
            
            for line in go_code.splitlines():
                if skip_header:
                    if line.startswith('package ') or line.startswith('import '):
                        continue
                    elif line.strip() and not line.strip().startswith('//'):
                        skip_header = False
                        code_lines.append(line)
                else:
                    code_lines.append(line)
            
            if code_lines:
                parts.append('\n'.join(code_lines))
                parts.append('')  # Add spacing between chunks
        
        return '\n'.join(parts)
