"""
Dependency Analyzer
Uses Python AST to analyze dependencies, imports, and relationships
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
from collections import defaultdict


class DependencyAnalyzer:
    """Analyzes Python code dependencies using AST"""
    
    def __init__(self, config, logger):
        """
        Initialize dependency analyzer
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.dependency_log_file = None
        
    def analyze(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze dependencies for all files
        
        Args:
            files: List of file information from scanner
            
        Returns:
            Dictionary with dependency analysis results
        """
        from ..utils.logger import get_timestamped_filename
        
        self.logger.info(f"Analyzing dependencies for {len(files)} files")
        
        # Create dependency log
        log_dir = self.config.get('LOG_DIR')
        self.dependency_log_file = log_dir / get_timestamped_filename('dependency', 'log')
        
        results = {
            'files': {},
            'total_dependencies': 0,
            'import_graph': defaultdict(list),
            'class_hierarchy': {},
            'function_calls': defaultdict(list),
            'log_file': str(self.dependency_log_file),
            'timestamp': datetime.now().isoformat()
        }
        
        # Analyze each file
        for file_info in files:
            if not file_info.get('valid_syntax', False):
                continue
            
            file_path = Path(file_info['path'])
            analysis = self._analyze_file(file_path)
            
            if analysis:
                results['files'][str(file_path)] = analysis
                results['total_dependencies'] += len(analysis['imports'])
                
                # Build import graph
                for imp in analysis['imports']:
                    results['import_graph'][file_info['name']].append(imp['module'])
        
        # Write dependency log
        self._write_dependency_log(results)
        
        self.logger.info(f"Dependency analysis complete: {results['total_dependencies']} dependencies found")
        return results
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze single file for dependencies
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Analysis results dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                'imports': self._extract_imports(tree),
                'classes': self._extract_classes(tree),
                'functions': self._extract_functions(tree),
                'function_calls': self._extract_function_calls(tree),
                'docstrings': self._extract_docstrings(tree),
            }
            
            self.logger.debug(f"Analyzed: {file_path.name}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract all imports from AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
        
        return imports
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'bases': [self._get_name(base) for base in node.bases],
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node)
                })
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions (top-level only)"""
        functions = []
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node)
                })
        
        return functions
    
    def _extract_function_calls(self, tree: ast.AST) -> List[str]:
        """Extract function/method calls"""
        calls = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._get_name(node.func)
                if call_name:
                    calls.add(call_name)
        
        return list(calls)
    
    def _extract_docstrings(self, tree: ast.AST) -> Dict[str, str]:
        """Extract module-level docstring"""
        docstring = ast.get_docstring(tree)
        return {'module': docstring} if docstring else {}
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ''
    
    def prepare_context(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare summarized context for AI conversion
        
        Args:
            analysis_results: Results from dependency analysis
            
        Returns:
            Summarized context dictionary
        """
        self.logger.info("Preparing context for AI conversion")
        
        context = {
            'file_count': len(analysis_results['files']),
            'total_classes': 0,
            'total_functions': 0,
            'key_modules': [],
            'business_domains': self._identify_business_domains(analysis_results),
            'shared_dependencies': self._identify_shared_dependencies(analysis_results),
        }
        
        # Summarize files
        for file_path, analysis in analysis_results['files'].items():
            context['total_classes'] += len(analysis['classes'])
            context['total_functions'] += len(analysis['functions'])
            
            # Identify key modules (with classes or many functions)
            if analysis['classes'] or len(analysis['functions']) > 3:
                context['key_modules'].append({
                    'file': Path(file_path).name,
                    'classes': [c['name'] for c in analysis['classes']],
                    'functions': [f['name'] for f in analysis['functions']],
                })
        
        return context
    
    def _identify_business_domains(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Identify business domains from file names and imports"""
        domains = set()
        
        keywords = {
            'invoice': 'Invoice Management',
            'ledger': 'General Ledger',
            'tax': 'Tax Calculation',
            'party': 'Party Management',
            'payment': 'Payment Processing',
            'account': 'Account Management',
            'journal': 'Journal Entries',
        }
        
        for file_path in analysis_results['files'].keys():
            file_name = Path(file_path).name.lower()
            for keyword, domain in keywords.items():
                if keyword in file_name:
                    domains.add(domain)
        
        return list(domains)
    
    def _identify_shared_dependencies(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Identify commonly imported modules"""
        import_counts = defaultdict(int)
        
        for analysis in analysis_results['files'].values():
            for imp in analysis['imports']:
                module = imp.get('module', '')
                if module and not module.startswith('.'):
                    import_counts[module] += 1
        
        # Get top 10 most common
        common = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [module for module, count in common if count > 1]
    
    def _write_dependency_log(self, results: Dict[str, Any]):
        """Write dependency analysis to log file"""
        with open(self.dependency_log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("DEPENDENCY ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Total Files Analyzed: {len(results['files'])}\n")
            f.write(f"Total Dependencies: {results['total_dependencies']}\n\n")
            
            f.write("IMPORT GRAPH:\n")
            for file, imports in results['import_graph'].items():
                f.write(f"\n{file}:\n")
                for imp in imports:
                    f.write(f"  → {imp}\n")
            
            f.write("\n" + "="*80 + "\n\n")
            
            f.write("FILE DETAILS:\n\n")
            for file_path, analysis in results['files'].items():
                f.write(f"File: {Path(file_path).name}\n")
                f.write(f"  Imports: {len(analysis['imports'])}\n")
                f.write(f"  Classes: {len(analysis['classes'])}\n")
                f.write(f"  Functions: {len(analysis['functions'])}\n")
                
                if analysis['classes']:
                    f.write("  Class Details:\n")
                    for cls in analysis['classes']:
                        f.write(f"    - {cls['name']} (line {cls['line']})\n")
                        if cls['bases']:
                            f.write(f"      Inherits from: {', '.join(cls['bases'])}\n")
                        if cls['methods']:
                            f.write(f"      Methods: {', '.join(cls['methods'][:5])}\n")
                
                f.write("\n")
