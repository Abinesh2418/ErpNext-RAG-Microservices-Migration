"""
Redis Store
Handles caching of file hashes, AST results, dependency graphs, and conversion outputs
"""

import hashlib
import json
import redis
from typing import Dict, List, Any, Optional
from datetime import datetime


class RedisStore:
    """Redis-based caching for incremental conversion"""
    
    def __init__(self, config, logger):
        """
        Initialize Redis store
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.client = None
        
        # Initialize Redis client
        try:
            redis_host = self.config.get('REDIS_HOST', 'localhost')
            redis_port = int(self.config.get('REDIS_PORT', 6379))
            redis_db = int(self.config.get('REDIS_DB', 0))
            
            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            
            # Test connection
            self.client.ping()
            self.logger.info(f"Redis connected: {redis_host}:{redis_port}/{redis_db}")
        except Exception as e:
            self.client = None
            self.logger.warning(f"Redis initialization failed: {e} - caching disabled")
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.client is not None
    
    # ========================================
    # FILE HASHING
    # ========================================
    
    def compute_file_hash(self, file_path: str, content: str) -> str:
        """
        Compute SHA-256 hash of file content
        
        Args:
            file_path: Path to file
            content: File content
            
        Returns:
            SHA-256 hash as hex string
        """
        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8'))
        return hasher.hexdigest()
    
    def file_changed(self, file_path: str, content: str) -> bool:
        """
        Check if file has changed since last processing
        
        Args:
            file_path: Path to file
            content: Current file content
            
        Returns:
            True if file changed, False if unchanged
        """
        if not self.is_available():
            return True  # Treat as changed if Redis unavailable
        
        try:
            # Compute current hash
            current_hash = self.compute_file_hash(file_path, content)
            
            # Get stored hash
            key = f"file_hash:{file_path}"
            stored_hash = self.client.get(key)
            
            if stored_hash is None:
                # First time seeing this file
                self.client.set(key, current_hash)
                return True
            
            if stored_hash != current_hash:
                # File changed - update hash
                self.client.set(key, current_hash)
                return True
            
            # File unchanged
            return False
        except Exception as e:
            self.logger.error(f"Failed to check file hash: {e}")
            return True  # Treat as changed on error
    
    # ========================================
    # AST CACHING
    # ========================================
    
    def get_cached_ast(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get cached AST result for file
        
        Args:
            file_path: Path to file
            
        Returns:
            Cached AST dict or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            key = f"ast:{file_path}"
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get cached AST: {e}")
            return None
    
    def set_cached_ast(self, file_path: str, ast_result: Dict[str, Any]) -> bool:
        """
        Cache AST result for file
        
        Args:
            file_path: Path to file
            ast_result: AST analysis result
            
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            key = f"ast:{file_path}"
            self.client.set(key, json.dumps(ast_result))
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache AST: {e}")
            return False
    
    # ========================================
    # DEPENDENCY GRAPH
    # ========================================
    
    def get_dependency_graph(self) -> Optional[Dict[str, List[str]]]:
        """
        Get cached dependency graph
        
        Returns:
            Dependency graph dict or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            key = "dependency_graph"
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get dependency graph: {e}")
            return None
    
    def set_dependency_graph(self, graph: Dict[str, List[str]]) -> bool:
        """
        Cache dependency graph
        
        Args:
            graph: Dependency graph mapping file -> [dependencies]
            
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            key = "dependency_graph"
            self.client.set(key, json.dumps(graph))
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache dependency graph: {e}")
            return False
    
    # ========================================
    # CONVERSION OUTPUT CACHING
    # ========================================
    
    def get_conversion_output(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get cached conversion output for file
        
        Args:
            file_path: Path to source file
            
        Returns:
            Cached conversion dict or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            key = f"conversion:{file_path}"
            cached = self.client.get(key)
            if cached:
                self.logger.info(f"Cache HIT: Conversion output for {file_path}")
                return json.loads(cached)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get cached conversion: {e}")
            return None
    
    def store_conversion_output(self, file_path: str, go_code: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cache conversion output
        
        Args:
            file_path: Path to source file
            go_code: Generated Go code
            metadata: Optional conversion metadata
            
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            key = f"conversion:{file_path}"
            conversion_data = {
                'go_code': go_code,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self.client.set(key, json.dumps(conversion_data))
            self.logger.debug(f"Cached conversion output for {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache conversion: {e}")
            return False
    
    # ========================================
    # CACHE MANAGEMENT
    # ========================================
    
    def clear_file_cache(self, file_path: str) -> bool:
        """
        Clear all cached data for a specific file
        
        Args:
            file_path: Path to file
            
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            keys = [
                f"file_hash:{file_path}",
                f"ast:{file_path}",
                f"conversion:{file_path}"
            ]
            self.client.delete(*keys)
            self.logger.info(f"Cleared cache for {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False
    
    def clear_all_cache(self) -> bool:
        """
        Clear all cached data (use with caution)
        
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            self.client.flushdb()
            self.logger.warning("Cleared all Redis cache")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear all cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.is_available():
            return {'available': False}
        
        try:
            info = self.client.info()
            return {
                'available': True,
                'used_memory': info.get('used_memory_human', 'N/A'),
                'total_keys': self.client.dbsize(),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {'available': False, 'error': str(e)}
