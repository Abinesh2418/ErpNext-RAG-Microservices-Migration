# RAG System Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Query Processing Pipeline](#query-processing-pipeline)
6. [Document Processing Workflow](#document-processing-workflow)
7. [Vector Storage](#vector-storage)
8. [Integration Points](#integration-points)
9. [Technology Stack](#technology-stack)
10. [Performance Considerations](#performance-considerations)

---

## System Overview

### Purpose
The RAG (Retrieval-Augmented Generation) system provides intelligent code search and context retrieval for ERPNext codebase analysis. It enables semantic search across documentation and code, enhancing AI-powered development assistance.

### Key Objectives
- **Semantic Search**: Find relevant code/docs using natural language queries
- **Context Retrieval**: Provide relevant context for AI-powered tasks
- **Knowledge Base**: Maintain searchable index of codebase documentation
- **Fast Retrieval**: Sub-second query response times
- **Accuracy**: High relevance in search results

### Core Principles
1. **Vector-Based Search**: Semantic embeddings for intelligent matching
2. **Local-First**: No external dependencies, runs locally
3. **Incremental Updates**: Add documents without full re-indexing
4. **Extensible**: Easy to add new document types
5. **Lightweight**: Minimal resource footprint

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG SYSTEM ARCHITECTURE                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              QUERY INTERFACE                        │   │
│  │  • Natural language queries                         │   │
│  │  • Code search                                      │   │
│  │  • Documentation lookup                             │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐   │
│  │           QUERY PROCESSING ENGINE                   │   │
│  │  • Query embedding generation                       │   │
│  │  • Vector similarity search                         │   │
│  │  • Result ranking & filtering                       │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐   │
│  │            VECTOR DATABASE (LanceDB)                │   │
│  │  • Document vectors (embeddings)                    │   │
│  │  • Metadata (file, type, location)                  │   │
│  │  • Fast ANN search                                  │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐   │
│  │         DOCUMENT PROCESSING PIPELINE                │   │
│  │  • Text extraction                                  │   │
│  │  • Chunking strategy                                │   │
│  │  • Embedding generation                             │   │
│  │  • Metadata extraction                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL COMPONENTS                         │
│                                                             │
│  • Sentence-Transformers (Embeddings)                       │
│  • Groq API (LLM for enhancement)                          │
│  • LanceDB (Vector storage)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Document Processing (`rag_system.py`)

**Responsibility**: Index and manage documents

```python
class RAGSystem:
    - index_documents()    # Add documents to vector DB
    - query()              # Search for relevant docs
    - update_index()       # Incremental updates
    - get_stats()          # System statistics
```

**Key Functions**:
- Document ingestion from various sources
- Text chunking and preprocessing
- Embedding generation
- Vector storage management

### 2. Query Engine (`rag_query.py`)

**Responsibility**: Process queries and retrieve results

```python
class RAGQuery:
    - embed_query()        # Convert query to vector
    - search()             # Vector similarity search
    - rank_results()       # Relevance ranking
    - format_response()    # Structure output
```

**Key Functions**:
- Query understanding
- Vector similarity computation
- Result filtering and ranking
- Context preparation for LLM

### 3. Document Loader

**Responsibility**: Load and parse different document types

**Supported Formats**:
- Markdown (.md)
- Python code (.py)
- Text files (.txt)
- JSON documentation (.json)

**Processing Steps**:
```
Load File → Parse Content → Extract Metadata → 
Chunk Text → Generate Embeddings → Store in DB
```

---

## Data Flow

### Indexing Flow

```
Document Input
     │
     ▼
┌──────────────────┐
│  Document Loader │
│  • Read file     │
│  • Parse format  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Text Processor  │
│  • Clean text    │
│  • Chunk content │
│  • Add metadata  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Embedding Engine │
│  • Generate      │
│    embeddings    │
│  • all-MiniLM    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Vector Storage  │
│  • LanceDB       │
│  • Index vectors │
│  • Store metadata│
└──────────────────┘
```

### Query Flow

```
User Query
     │
     ▼
┌──────────────────┐
│  Query Processor │
│  • Parse query   │
│  • Clean text    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Embedding Engine │
│  • Generate      │
│    query vector  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Vector Search   │
│  • Similarity    │
│  • Top-K results │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Result Ranker   │
│  • Score results │
│  • Filter        │
│  • Format output │
└────────┬─────────┘
         │
         ▼
    Results to User
```

---

## Query Processing Pipeline

### Step-by-Step Query Processing

```
STEP 1: QUERY NORMALIZATION
├─► Convert to lowercase
├─► Remove special characters
├─► Tokenization
└─► Query expansion (optional)

STEP 2: EMBEDDING GENERATION
├─► Use Sentence-Transformer model
├─► Generate 384-dim vector (all-MiniLM-L6-v2)
└─► Normalize vector

STEP 3: VECTOR SEARCH
├─► Compute cosine similarity
├─► Find top-K nearest neighbors
├─► Use LanceDB ANN index
└─► Retrieve candidate documents

STEP 4: RESULT RANKING
├─► Apply relevance scoring
├─► Filter by metadata (file type, domain)
├─► Re-rank by multiple factors:
│   ├─► Semantic similarity (70%)
│   ├─► Keyword match (20%)
│   └─► Recency/popularity (10%)
└─► Return top N results

STEP 5: CONTEXT PREPARATION
├─► Extract relevant snippets
├─► Add metadata (file, location)
├─► Format for LLM consumption
└─► Return structured response
```

---

## Document Processing Workflow

### Document Ingestion Pipeline

```
┌────────────────────────────────────────────────────────┐
│ DOCUMENT PROCESSING STAGES                             │
└────────────────────────────────────────────────────────┘

STAGE 1: DOCUMENT LOADING
Input: File path or directory
├─► Read file content
├─► Detect file type
├─► Parse structure (for code/markdown)
└─► Extract raw text

STAGE 2: TEXT PREPROCESSING
├─► Remove noise (HTML tags, special chars)
├─► Normalize whitespace
├─► Detect language
└─► Clean formatting

STAGE 3: CHUNKING STRATEGY
├─► Chunk by:
│   ├─► Paragraphs (for docs)
│   ├─► Functions/classes (for code)
│   └─► Sections (for markdown)
├─► Chunk size: 500-1000 tokens
├─► Overlap: 100 tokens
└─► Preserve context

STAGE 4: METADATA EXTRACTION
├─► File path and name
├─► Document type
├─► Section/function name
├─► Timestamps
└─► Custom tags

STAGE 5: EMBEDDING GENERATION
├─► Use all-MiniLM-L6-v2
├─► Generate 384-dim vectors
├─► Batch processing (32 docs/batch)
└─► Cache embeddings

STAGE 6: STORAGE
├─► Store in LanceDB
├─► Create indexes
├─► Save metadata
└─► Update statistics
```

### Chunking Strategy

```python
# For Markdown Documents
Chunk Strategy: By section headers
Chunk Size: 500-1000 tokens
Overlap: 100 tokens

# For Python Code
Chunk Strategy: By function/class
Chunk Size: Complete function/class
Overlap: None (preserve code structure)

# For Large Documents
Chunk Strategy: Sliding window
Chunk Size: 1000 tokens
Overlap: 200 tokens
```

---

## Vector Storage

### LanceDB Schema

```python
{
    "id": "unique_doc_id",
    "text": "document content",
    "vector": [384-dim embedding],
    "metadata": {
        "file_path": "path/to/file",
        "file_type": "markdown|python|text",
        "section": "section name",
        "created_at": "timestamp",
        "tags": ["tag1", "tag2"]
    }
}
```

### Storage Organization

```
rag_system/
├── lancedb/                    # Vector database
│   ├── documents.lance         # Main document store
│   ├── _versions/              # Version control
│   └── _indices/               # Search indices
└── cache/                      # Embedding cache
    └── embeddings.pkl
```

### Index Types

1. **Vector Index (ANN)**
   - Algorithm: IVF (Inverted File Index)
   - Distance metric: Cosine similarity
   - Performance: O(log n) search time

2. **Metadata Index**
   - File path index
   - Type filter
   - Tag-based filtering

---

## Integration Points

### 1. VS Code Extension Integration

```javascript
// In VS Code extension
const ragQuery = await fetch('http://localhost:8000/rag/query', {
    method: 'POST',
    body: JSON.stringify({
        query: userQuery,
        limit: 5
    })
});
```

### 2. AI-Modernization Integration

```python
# In AI-Modernization backend
from rag_system import RAGSystem

rag = RAGSystem()
context = rag.query("How to implement invoice validation?")

# Use context in LLM prompt
prompt = f"Context: {context}\n\nQuestion: {user_question}"
```

### 3. Accounts-Modernization Integration

```python
# In Accounts-Modernization converter
from rag_system import RAGQuery

rag_query = RAGQuery()
similar_code = rag_query.search(
    query="party customer management",
    limit=3,
    filter_type="python"
)

# Use similar code as conversion context
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Embeddings** | Sentence-Transformers | Text → Vector conversion |
| **Model** | all-MiniLM-L6-v2 | 384-dim embeddings |
| **Vector DB** | LanceDB | Local vector storage |
| **LLM** | Groq API (optional) | Query enhancement |
| **Language** | Python 3.8+ | System implementation |

### Dependencies

```python
# Core
sentence-transformers >= 2.2.0
lancedb >= 0.3.0

# Optional
groq >= 0.4.0          # For LLM enhancement
langchain >= 0.3.0     # For advanced features
```

---

## Performance Considerations

### Query Performance

```
Target Metrics:
├─► Query latency: <100ms (p95)
├─► Embedding generation: <50ms
├─► Vector search: <30ms
├─► Result ranking: <20ms
└─► Total response: <100ms
```

### Scaling Considerations

```
Small Dataset (< 1000 docs):
├─► In-memory vector search
├─► No index optimization needed
└─► Response time: <50ms

Medium Dataset (1K - 100K docs):
├─► IVF index with 100 centroids
├─► Batch embedding generation
└─► Response time: <100ms

Large Dataset (> 100K docs):
├─► IVF index with 1000 centroids
├─► Distributed search (future)
└─► Response time: <200ms
```

### Optimization Strategies

1. **Embedding Cache**
   ```python
   # Cache frequently queried embeddings
   cache = {}
   if query in cache:
       embedding = cache[query]
   else:
       embedding = model.encode(query)
       cache[query] = embedding
   ```

2. **Batch Processing**
   ```python
   # Process documents in batches
   batch_size = 32
   for batch in chunks(documents, batch_size):
       embeddings = model.encode(batch)
   ```

3. **Index Optimization**
   ```python
   # Create ANN index for faster search
   table.create_index(
       metric="cosine",
       num_partitions=100
   )
   ```

---

## Query Examples

### Example 1: Simple Query

```python
from rag_system import RAGQuery

rag = RAGQuery()
results = rag.search("How to create a sales invoice?", limit=5)

for result in results:
    print(f"File: {result['file_path']}")
    print(f"Content: {result['text'][:200]}...")
    print(f"Score: {result['score']}")
```

### Example 2: Filtered Query

```python
# Search only in Python files
results = rag.search(
    query="invoice validation logic",
    limit=5,
    filter={"file_type": "python"}
)
```

### Example 3: Code Search

```python
# Find similar code patterns
results = rag.search(
    query="def calculate_tax",
    limit=3,
    filter={"file_type": "python", "section": "function"}
)
```

---

## System Workflow Diagram

```
USER INTERACTION
       │
       ▼
┌─────────────────┐
│  Query Input    │
│  "Find invoice  │
│   validation"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Query Processor │
│ • Normalize     │
│ • Embed         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Search   │
│ • ANN search    │
│ • Top-K results │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Result Ranker   │
│ • Score         │
│ • Filter        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Builder │
│ • Format        │
│ • Add metadata  │
└────────┬────────┘
         │
         ▼
    RESPONSE
```

---

## Future Enhancements

### Phase 1: Current (Implemented)
- ✅ Basic vector search
- ✅ Document indexing
- ✅ Query processing

### Phase 2: Near-term
- ⏳ Hybrid search (vector + keyword)
- ⏳ Query expansion
- ⏳ Relevance feedback

### Phase 3: Long-term
- 🔮 Multi-modal search (code + docs + images)
- 🔮 Distributed indexing
- 🔮 Real-time updates

---

## Conclusion

The RAG system provides a robust, scalable solution for semantic search across ERPNext codebase documentation. Its vector-based approach enables intelligent retrieval, while the local-first architecture ensures privacy and performance.

**Key Benefits:**
1. ✅ Fast semantic search (<100ms)
2. ✅ Local execution (no cloud dependency)
3. ✅ Extensible architecture
4. ✅ High accuracy retrieval
5. ✅ Easy integration

**Target Use Cases:**
- Code search and discovery
- Documentation lookup
- Context retrieval for AI assistants
- Knowledge base queries
- Similar code pattern finding
