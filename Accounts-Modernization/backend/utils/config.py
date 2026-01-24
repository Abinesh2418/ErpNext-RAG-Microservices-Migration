"""
Configuration Manager for Accounts-Modernization
Loads and manages environment variables and system configuration
"""

import os
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager"""
    
    def __init__(self):
        """Initialize configuration"""
        # Get project root (Accounts-Modernization directory)
        # Path: backend/utils/config.py -> backend/ -> Accounts-Modernization/
        self.project_root = Path(__file__).parent.parent.parent
        
        # Get root directory (parent of Accounts-Modernization)
        # This is: Erpnext-Refactoring/
        self.root_dir = self.project_root.parent
        
        # Load environment variables from root directory's .env file
        root_env_file = self.root_dir / '.env'
        if root_env_file.exists():
            load_dotenv(dotenv_path=root_env_file)
        else:
            # Fallback: load from current directory
            load_dotenv()
        
        # Set up directories (outside backend folder)
        self.dirs = {
            'LOG_DIR': self.project_root / 'logs',
            'RESULTS_DIR': self.project_root / 'results',
            'MODERN_DIR': self.project_root / 'modern',
            'TESTS_DIR': self.project_root / 'tests',
        }
        
        # Create directories if they don't exist
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load configuration from environment
        self.config = {
            # AI Configuration
            'GROQ_API_KEY': os.getenv('GROQ_API_KEY', ''),
            'GROQ_MODEL': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
            'EMBEDDING_MODEL': os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
            'MAX_CONTEXT_TOKENS': int(os.getenv('MAX_CONTEXT_TOKENS', '8000')),
            'AI_TEMPERATURE': float(os.getenv('AI_TEMPERATURE', '0.7')),
            
            # Conversion Configuration
            'MAX_FILE_SIZE_MB': int(os.getenv('MAX_FILE_SIZE_MB', '10')),
            'ENABLE_SYNTAX_CHECK': os.getenv('ENABLE_SYNTAX_CHECK', 'true').lower() == 'true',
            'ENABLE_COMPILE_CHECK': os.getenv('ENABLE_COMPILE_CHECK', 'true').lower() == 'true',
            'MAX_RETRY_ATTEMPTS': int(os.getenv('MAX_RETRY_ATTEMPTS', '3')),
            
            # Logging
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            
            # Directories
            **self.dirs
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
    
    def get_all(self) -> dict:
        """
        Get all configuration
        
        Returns:
            Dictionary of all configuration
        """
        return self.config.copy()