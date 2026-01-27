"""
Pre-Indexing System
Scans all Python files and indexes them in Qdrant before conversion
Builds complete semantic knowledge base for context-aware conversion
"""

import ast
import time
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict


class PreIndexer:
    """Pre-indexes all Python files into Qdrant before conversion"""
    
    def __init__(self, config, logger, qdrant_index):
        """
        Initialize pre-indexer
        
        Args:
            config: Configuration object
            logger: Logger instance
            qdrant_index: QdrantIndex instance
        """
        self.config = config
        self.logger = logger
        self.qdrant_index = qdrant_index
    
    def index_all_files(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pre-index all Python files into Qdrant
        
        Args:
            files: List of file information from scanner
            
        Returns:
            Indexing statistics
        """
        self.logger.info(f"🔍 Pre-indexing {len(files)} files into Qdrant...")
        start_time = time.time()
        
        if not self.qdrant_index.is_available():
            self.logger.warning("Qdrant not available - skipping pre-indexing")
            return {
                'indexed_files': 0,
                'indexed_functions': 0,
                'indexed_classes': 0,
                'skipped': len(files),
                'elapsed_time': 0
            }
        
        indexed_files = 0
        indexed_functions = 0
        indexed_classes = 0
        skipped = 0
        
        for file_info in files:
            if not file_info.get('valid_syntax', False):
                skipped += 1
                continue
            
            try:
                file_path = file_info['path']
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST
                tree = ast.parse(content, filename=file_path)
                
                # Extract and index file meaning
                file_meaning = self._generate_file_meaning(file_info, tree)
                self.qdrant_index.store_file_meaning(file_path, file_meaning)
                indexed_files += 1
                
                # Extract and index functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_meaning = self._generate_function_meaning(node)
                        self.qdrant_index.store_function_meaning(
                            file_path,
                            node.name,
                            func_meaning
                        )
                        indexed_functions += 1
                    
                    elif isinstance(node, ast.ClassDef):
                        class_meaning = self._generate_class_meaning(node)
                        # Store class as special function type
                        self.qdrant_index.store_function_meaning(
                            file_path,
                            f"class_{node.name}",
                            class_meaning
                        )
                        indexed_classes += 1
                
                self.logger.info(f"  ✓ Indexed: {file_info['name']}")
                
            except Exception as e:
                self.logger.error(f"  ✗ Failed to index {file_info['name']}: {e}")
                skipped += 1
        
        elapsed_time = time.time() - start_time
        
        self.logger.info(
            f"✓ Pre-indexing complete: {indexed_files} files, "
            f"{indexed_functions} functions, {indexed_classes} classes "
            f"in {elapsed_time:.2f}s"
        )
        
        return {
            'indexed_files': indexed_files,
            'indexed_functions': indexed_functions,
            'indexed_classes': indexed_classes,
            'skipped': skipped,
            'elapsed_time': elapsed_time
        }
    
    def _generate_file_meaning(self, file_info: Dict[str, Any], tree: ast.AST) -> str:
        """Generate semantic meaning for a file"""
        filename = Path(file_info['name']).stem
        
        # Extract module docstring
        docstring = ast.get_docstring(tree) or ""
        
        # Count elements
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        
        # Detect business domain
        domain = self._detect_domain(filename, docstring)
        
        # Generate meaning
        meaning = f"File {filename}: {domain}. "
        if docstring:
            meaning += f"{docstring[:100]}. "
        meaning += f"Contains {functions} functions and {classes} classes."
        
        return meaning
    
    def _generate_function_meaning(self, node: ast.FunctionDef) -> str:
        """Generate semantic meaning for a function"""
        docstring = ast.get_docstring(node) or ""
        
        # Get function signature
        args = [arg.arg for arg in node.args.args]
        
        meaning = f"Function {node.name}("
        meaning += ", ".join(args) if args else ""
        meaning += "): "
        
        if docstring:
            meaning += docstring[:150]
        else:
            # Generate meaning from function name
            meaning += self._infer_function_purpose(node.name)
        
        return meaning
    
    def _generate_class_meaning(self, node: ast.ClassDef) -> str:
        """Generate semantic meaning for a class"""
        docstring = ast.get_docstring(node) or ""
        
        # Count methods
        methods = sum(1 for item in node.body if isinstance(item, ast.FunctionDef))
        
        meaning = f"Class {node.name}: "
        
        if docstring:
            meaning += docstring[:150]
        else:
            meaning += self._infer_class_purpose(node.name)
        
        meaning += f" Contains {methods} methods."
        
        return meaning
    
    def _detect_domain(self, filename: str, docstring: str) -> str:
        """Detect business domain from filename and docstring"""
        text = (filename + " " + docstring).lower()
        
        if any(word in text for word in ['invoice', 'sales', 'purchase']):
            return "Invoice processing"
        elif any(word in text for word in ['ledger', 'journal', 'entry']):
            return "Ledger management"
        elif any(word in text for word in ['tax', 'vat', 'gst']):
            return "Tax calculation"
        elif any(word in text for word in ['party', 'customer', 'supplier']):
            return "Party management"
        elif any(word in text for word in ['payment', 'receipt']):
            return "Payment handling"
        else:
            return "Accounting utility"
    
    def _infer_function_purpose(self, func_name: str) -> str:
        """Infer function purpose from name"""
        name_lower = func_name.lower()
        
        if name_lower.startswith('get_'):
            return "Retrieves data"
        elif name_lower.startswith('set_'):
            return "Sets data"
        elif name_lower.startswith('validate_'):
            return "Validates business rules"
        elif name_lower.startswith('calculate_'):
            return "Performs calculations"
        elif name_lower.startswith('make_'):
            return "Creates entries"
        elif name_lower.startswith('update_'):
            return "Updates records"
        elif name_lower.startswith('delete_'):
            return "Deletes records"
        else:
            return "Performs business logic"
    
    def _infer_class_purpose(self, class_name: str) -> str:
        """Infer class purpose from name"""
        name_lower = class_name.lower()
        
        if 'service' in name_lower:
            return "Service layer for business logic"
        elif 'controller' in name_lower:
            return "Controller for request handling"
        elif 'manager' in name_lower:
            return "Manager for coordinating operations"
        elif 'validator' in name_lower:
            return "Validator for business rules"
        else:
            return "Data model or utility class"


class DependencyScheduler:
    """Schedules files for conversion based on dependency levels"""
    
    def __init__(self, logger):
        """
        Initialize dependency scheduler
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def build_dependency_levels(self, dependency_graph: Dict[str, Any], scanned_files: List[Dict[str, Any]] = None) -> List[List[str]]:
        """
        Build dependency levels for parallel conversion
        
        Args:
            dependency_graph: Dependency graph from analyzer (supports both 'file_dependencies' and 'import_graph')
            scanned_files: Optional list of actually scanned files to filter against
            
        Returns:
            List of levels, each level contains files that can be converted in parallel
        """
        self.logger.info("📊 Building dependency levels for parallel conversion...")
        
        # Build set of actual file identifiers if provided
        actual_files = set()
        if scanned_files:
            for f in scanned_files:
                actual_files.add(f['path'])
                actual_files.add(f['name'])
                actual_files.add(Path(f['name']).stem)
                actual_files.add(str(Path(f['path'])))
            self.logger.info(f"📂 Filtering against {len(scanned_files)} actually scanned files")
        
        # Extract file dependencies (supports both formats)
        file_dependencies = dependency_graph.get('file_dependencies', dependency_graph.get('import_graph', {}))
        
        # Build reverse dependency map (who depends on whom)
        depends_on = defaultdict(set)
        depended_by = defaultdict(set)
        all_files = set()
        
        for file_path, deps in file_dependencies.items():
            # Only include if we have this file in scanned_files (or no filter)
            if not scanned_files or file_path in actual_files:
                all_files.add(file_path)
                for dep in deps:
                    depends_on[file_path].add(dep)
                    depended_by[dep].add(file_path)
                    # Only add dep to all_files if it's also in scanned_files
                    if not scanned_files or dep in actual_files:
                        all_files.add(dep)
        
        # If we have scanned_files but no files in all_files, use scanned files directly
        if scanned_files and not all_files:
            self.logger.warning("⚠️  No dependency matches found, using scanned files directly")
            # Return all scanned files as a single level
            return [[f['path'] for f in scanned_files]]
        
        # Calculate dependency levels using topological sort
        levels = []
        processed = set()
        
        while len(processed) < len(all_files):
            # Find files with no unprocessed dependencies
            current_level = []
            for file_path in all_files:
                if file_path in processed:
                    continue
                
                # Check if all dependencies are processed
                file_deps = depends_on.get(file_path, set())
                if all(dep in processed for dep in file_deps):
                    current_level.append(file_path)
            
            if not current_level:
                # Circular dependency or isolated files - add remaining
                remaining = all_files - processed
                current_level = list(remaining)
                self.logger.warning(
                    f"⚠️  Circular dependencies detected, "
                    f"processing {len(current_level)} files together"
                )
            
            levels.append(current_level)
            processed.update(current_level)
        
        # Log level statistics
        self.logger.info(f"✓ Created {len(levels)} dependency levels:")
        for i, level in enumerate(levels):
            self.logger.info(f"  Level {i}: {len(level)} files (parallel)")
            self.logger.debug(f"    Files: {level[:3]}...")  # Show first 3
        
        return levels
    
    def classify_files_by_complexity(self, files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Classify files by complexity for model selection
        
        Args:
            files: List of file information
            
        Returns:
            Dictionary with 'simple' and 'complex' file lists
        """
        simple_files = []
        complex_files = []
        
        for file_info in files:
            lines = file_info.get('lines', 0)
            
            # Simple files: < 200 lines (use fast model)
            # Complex files: >= 200 lines (use smart model)
            if lines < 200:
                simple_files.append(file_info['path'])
            else:
                complex_files.append(file_info['path'])
        
        self.logger.info(
            f"📊 File complexity: {len(simple_files)} simple, {len(complex_files)} complex"
        )
        
        return {
            'simple': simple_files,
            'complex': complex_files
        }
