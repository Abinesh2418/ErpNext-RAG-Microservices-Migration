"""
Accounts Scanner
Scans ERPNext Accounts module to identify Python files and structure
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class AccountsScanner:
    """Scanner for ERPNext Accounts module"""
    
    def __init__(self, config, logger):
        """
        Initialize scanner
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.scan_log_file = None
        
    def scan(self, path: str) -> Dict[str, Any]:
        """
        Scan accounts module or file
        
        Args:
            path: Path to file or directory
            
        Returns:
            Dictionary with scan results
        """
        from ..utils.logger import get_timestamped_filename
        
        self.logger.info(f"Starting scan of: {path}")
        
        # Create scan log
        log_dir = self.config.get('LOG_DIR')
        self.scan_log_file = log_dir / get_timestamped_filename('scan', 'log')
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        files = []
        
        if path_obj.is_file():
            if path_obj.suffix == '.py':
                files.append(self._scan_file(path_obj))
        else:
            files = self._scan_directory(path_obj)
        
        # Write scan log
        self._write_scan_log(files)
        
        result = {
            'path': str(path),
            'file_count': len(files),
            'files': files,
            'log_file': str(self.scan_log_file),
            'timestamp': datetime.now().isoformat()
        }
        
        # After scanning, check if any files found
        if len(files) == 0:
            self.logger.warning(f"No Python files found in {path}")
            result['warning'] = 'No Python files found'
        
        self.logger.info(f"Scan complete: {len(files)} files found")
        return result
    
    def _scan_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """
        Recursively scan directory for Python files
        
        Args:
            directory: Directory path
            
        Returns:
            List of file information dictionaries
        """
        files = []
        
        for item in directory.rglob('*.py'):
            if item.is_file():
                # Skip __pycache__ and test files for now
                if '__pycache__' not in str(item):
                    file_info = self._scan_file(item)
                    if file_info:
                        files.append(file_info)
        
        return files
    
    def _scan_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan individual Python file
        
        Args:
            file_path: Path to Python file
            
        Returns:
            File information dictionary
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse with AST to validate syntax
            tree = ast.parse(content)
            
            # Extract basic information
            info = {
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'lines': len(content.splitlines()),
                'language': 'python',
                'valid_syntax': True,
                'has_classes': any(isinstance(node, ast.ClassDef) for node in ast.walk(tree)),
                'has_functions': any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree)),
            }
            
            self.logger.debug(f"Scanned: {file_path.name}")
            return info
            
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {e}")
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'language': 'python',
                'valid_syntax': False,
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Error scanning {file_path}: {e}")
            return None
    
    def _write_scan_log(self, files: List[Dict[str, Any]]):
        """
        Write scan results to log file
        
        Args:
            files: List of file information
        """
        with open(self.scan_log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ACCOUNTS MODULE SCAN REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Total Files: {len(files)}\n")
            f.write(f"Valid Python Files: {sum(1 for f in files if f.get('valid_syntax', False))}\n")
            f.write(f"Files with Classes: {sum(1 for f in files if f.get('has_classes', False))}\n")
            f.write(f"Files with Functions: {sum(1 for f in files if f.get('has_functions', False))}\n")
            f.write("\n" + "-"*80 + "\n\n")
            
            f.write("FILE DETAILS:\n\n")
            for file_info in files:
                f.write(f"File: {file_info['name']}\n")
                f.write(f"  Path: {file_info['path']}\n")
                f.write(f"  Size: {file_info['size']} bytes\n")
                if 'lines' in file_info:
                    f.write(f"  Lines: {file_info['lines']}\n")
                f.write(f"  Valid: {file_info.get('valid_syntax', 'Unknown')}\n")
                if 'has_classes' in file_info:
                    f.write(f"  Has Classes: {file_info['has_classes']}\n")
                if 'has_functions' in file_info:
                    f.write(f"  Has Functions: {file_info['has_functions']}\n")
                if 'error' in file_info:
                    f.write(f"  Error: {file_info['error']}\n")
                f.write("\n")
