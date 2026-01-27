"""
Qdrant Index
Stores semantic meaning (file-level, function-level, dependency meaning) for LLM context retrieval
Uses Ollama for embeddings generation
"""

import uuid
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    QDRANT_AVAILABLE = False


class QdrantIndex:
    """Qdrant-based semantic index for meaning storage and retrieval"""
    
    def __init__(self, config, logger):
        """
        Initialize Qdrant index
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.client = None
        self.embedding_model = None
        self.collection_name = "accounts_modernization"
        
        # Ollama configuration for embeddings
        self.ollama_base_url = self.config.get('OLLAMA_BASE_URL')
        self.ollama_embed_model = self.config.get('OLLAMA_EMBED_MODEL')
        self.ollama_embed_endpoint = f"{self.ollama_base_url}/api/embeddings"
        
        # Initialize Qdrant client
        if not QDRANT_AVAILABLE:
            self.logger.warning("Qdrant package not installed - semantic indexing disabled")
            return
        
        try:
            # Local Qdrant connection (Docker/native)
            qdrant_host = self.config.get('QDRANT_HOST', 'localhost')
            qdrant_port = self.config.get('QDRANT_PORT', 6333)
            
            self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
            self.logger.info(f"Qdrant connected: {qdrant_host}:{qdrant_port}")
            
            # Test Ollama embeddings
            test_embedding = self._generate_embedding("test")
            if not test_embedding:
                raise Exception("Failed to generate test embedding from Ollama")
            
            vector_size = len(test_embedding)
            self.logger.info(f"Ollama embeddings: {self.ollama_embed_model}, dimension: {vector_size}")
            
            # Mark embedding model as available (using Ollama)
            self.embedding_model = "ollama"
            
            # Create collection if it doesn't exist
            self._ensure_collection(vector_size)
            
            self.logger.info(f"✅ Qdrant ready with Ollama embeddings ({self.ollama_embed_model})")
        except Exception as e:
            self.client = None
            self.embedding_model = None
            self.logger.warning(f"Qdrant initialization failed: {e} - semantic indexing disabled")
    
    def is_available(self) -> bool:
        """Check if Qdrant is available"""
        return self.client is not None and self.embedding_model is not None
    
    def _ensure_collection(self, vector_size: int):
        """Ensure collection exists, create if not"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                self.logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                self.logger.debug(f"Qdrant collection exists: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to ensure collection: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Ollama
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list
        """
        try:
            response = requests.post(
                self.ollama_embed_endpoint,
                json={
                    "model": self.ollama_embed_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Ollama returns embedding in 'embedding' field
            embedding = result.get('embedding', [])
            if not embedding:
                self.logger.error(f"Empty embedding returned from Ollama")
                return []
            
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to generate embedding from Ollama: {e}")
            return []
    
    # ========================================
    # FILE-LEVEL MEANING
    # ========================================
    
    def store_file_meaning(self, file_path: str, meaning: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store semantic meaning for a file
        
        Args:
            file_path: Path to file
            meaning: Human-readable description (e.g., "Handles invoice creation and posting")
            metadata: Additional metadata (business_domain, functions, etc.)
            
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            # Generate embedding
            embedding = self._generate_embedding(meaning)
            if not embedding:
                return False
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'type': 'file',
                    'file_path': file_path,
                    'meaning': meaning,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata or {}
                }
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            self.logger.debug(f"Stored file meaning: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store file meaning: {e}")
            return False
    
    def get_file_meaning(self, file_path: str) -> Optional[str]:
        """
        Get stored meaning for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Meaning string or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            # Search by file_path filter
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="type", match=MatchValue(value="file")),
                        FieldCondition(key="file_path", match=MatchValue(value=file_path))
                    ]
                ),
                limit=1
            )
            
            if results[0]:  # results is a tuple (points, next_page_offset)
                return results[0][0].payload.get('meaning')
            return None
        except Exception as e:
            self.logger.error(f"Failed to get file meaning: {e}")
            return None
    
    # ========================================
    # FUNCTION-LEVEL MEANING
    # ========================================
    
    def store_function_meaning(self, file_path: str, function_name: str, meaning: str, 
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store semantic meaning for a function
        
        Args:
            file_path: Path to file containing function
            function_name: Name of function
            meaning: Human-readable description (e.g., "Calculates tax for invoice amount")
            metadata: Additional metadata (parameters, return_type, etc.)
            
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            # Generate embedding
            full_text = f"{function_name}: {meaning}"
            embedding = self._generate_embedding(full_text)
            if not embedding:
                return False
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'type': 'function',
                    'file_path': file_path,
                    'function_name': function_name,
                    'meaning': meaning,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata or {}
                }
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            self.logger.debug(f"Stored function meaning: {function_name} in {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store function meaning: {e}")
            return False
    
    # ========================================
    # DEPENDENCY MEANING
    # ========================================
    
    def store_dependency_meaning(self, from_file: str, to_file: str, meaning: str) -> bool:
        """
        Store semantic meaning of a dependency relationship
        
        Args:
            from_file: Source file path
            to_file: Target file path
            meaning: Description of the dependency (e.g., "Uses party ledger functions")
            
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            # Generate embedding
            full_text = f"Dependency from {from_file} to {to_file}: {meaning}"
            embedding = self._generate_embedding(full_text)
            if not embedding:
                return False
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'type': 'dependency',
                    'from_file': from_file,
                    'to_file': to_file,
                    'meaning': meaning,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            self.logger.debug(f"Stored dependency meaning: {from_file} -> {to_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store dependency meaning: {e}")
            return False
    
    # ========================================
    # SEMANTIC SEARCH & RETRIEVAL
    # ========================================
    
    def search_relevant_context(self, query: str, top_k: int = 5, 
                                filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for semantically relevant context
        
        Args:
            query: Search query (e.g., "invoice tax calculation")
            top_k: Number of results to return
            filter_type: Optional filter by type ('file', 'function', 'dependency')
            
        Returns:
            List of relevant context items with meaning and metadata
        """
        if not self.is_available():
            return []
        
        try:
            # Build filter
            search_filter = None
            if filter_type:
                search_filter = Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value=filter_type))]
                )
            
            # Search Qdrant using query_points with vector
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return []
            
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=search_filter,
                limit=top_k
            ).points
            
            # Format results
            context_items = []
            for result in results:
                context_items.append({
                    'score': result.score,
                    'type': result.payload.get('type'),
                    'meaning': result.payload.get('meaning'),
                    'file_path': result.payload.get('file_path'),
                    'function_name': result.payload.get('function_name'),
                    'metadata': result.payload.get('metadata', {}),
                    'timestamp': result.payload.get('timestamp')
                })
            
            self.logger.info(f"Found {len(context_items)} relevant context items for query: {query}")
            return context_items
        except Exception as e:
            self.logger.error(f"Failed to search relevant context: {e}")
            return []
    
    def get_file_context(self, file_path: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Get relevant context for a specific file being converted
        
        Args:
            file_path: File being converted
            top_k: Number of related items to retrieve
            
        Returns:
            List of relevant context from other files/functions
        """
        # First get the file's own meaning to use as query
        file_meaning = self.get_file_meaning(file_path)
        
        if not file_meaning:
            # Fallback to file name as query
            file_meaning = f"Context for {file_path}"
        
        # Search for related context
        return self.search_relevant_context(file_meaning, top_k=top_k)
    
    # ========================================
    # BATCH OPERATIONS
    # ========================================
    
    def store_batch_meanings(self, meanings: List[Dict[str, Any]]) -> int:
        """
        Store multiple meanings in batch
        
        Args:
            meanings: List of meaning dictionaries with type, content, metadata
            
        Returns:
            Number of successfully stored meanings
        """
        if not self.is_available():
            return 0
        
        success_count = 0
        for meaning_data in meanings:
            meaning_type = meaning_data.get('type')
            
            if meaning_type == 'file':
                success = self.store_file_meaning(
                    file_path=meaning_data.get('file_path'),
                    meaning=meaning_data.get('meaning'),
                    metadata=meaning_data.get('metadata')
                )
            elif meaning_type == 'function':
                success = self.store_function_meaning(
                    file_path=meaning_data.get('file_path'),
                    function_name=meaning_data.get('function_name'),
                    meaning=meaning_data.get('meaning'),
                    metadata=meaning_data.get('metadata')
                )
            elif meaning_type == 'dependency':
                success = self.store_dependency_meaning(
                    from_file=meaning_data.get('from_file'),
                    to_file=meaning_data.get('to_file'),
                    meaning=meaning_data.get('meaning')
                )
            else:
                success = False
            
            if success:
                success_count += 1
        
        self.logger.info(f"Batch stored {success_count}/{len(meanings)} meanings")
        return success_count
    
    # ========================================
    # INDEX MANAGEMENT
    # ========================================
    
    def delete_file_entries(self, file_path: str) -> int:
        """
        Delete all entries related to a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Number of deleted entries
        """
        if not self.is_available():
            return 0
        
        try:
            # Get all points for this file
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="file_path", match=MatchValue(value=file_path))]
                ),
                limit=100
            )
            
            # Delete points
            point_ids = [point.id for point in results[0]]
            if point_ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
            
            self.logger.info(f"Deleted {len(point_ids)} entries for {file_path}")
            return len(point_ids)
        except Exception as e:
            self.logger.error(f"Failed to delete file entries: {e}")
            return 0
    
    def clear_all_meanings(self) -> bool:
        """
        Clear all semantic meanings (use with caution)
        
        Returns:
            Success boolean
        """
        if not self.is_available():
            return False
        
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            
            # Recreate empty collection
            test_embedding = self._generate_embedding("test")
            if test_embedding:
                vector_size = len(test_embedding)
                self._ensure_collection(vector_size)
            
            self.logger.warning("Cleared all Qdrant meanings")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear meanings: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics
        
        Returns:
            Dictionary with index stats
        """
        if not self.is_available():
            return {'available': False}
        
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            
            # Count by type
            file_count = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value="file"))])
            )
            
            function_count = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value="function"))])
            )
            
            dependency_count = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value="dependency"))])
            )
            
            return {
                'available': True,
                'total_points': collection_info.points_count,
                'file_meanings': file_count.count,
                'function_meanings': function_count.count,
                'dependency_meanings': dependency_count.count,
                'vector_size': collection_info.config.params.vectors.size
            }
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {e}")
            return {'available': False, 'error': str(e)}
