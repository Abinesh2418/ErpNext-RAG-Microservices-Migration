import os
import sys
from pathlib import Path
import lancedb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from groq import Groq
from dotenv import load_dotenv

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Load environment variables from .env file
load_dotenv()


class ERPNextRAG:
    def __init__(self, groq_api_key=None, embedding_model_name=None):
        """
        Initialize RAG system with LanceDB and Groq
        
        Args:
            groq_api_key (str): Groq API key (reads from .env if not provided)
            embedding_model_name (str): Sentence Transformer model name
        """
        
        # Get API key from parameter or environment variable
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Get model configuration from environment
        self.llm_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        embedding_model = embedding_model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # 1. Load embedding model (FREE - runs locally)
        print("="*70, flush=True)
        print("📚 LOADING EMBEDDING MODEL", flush=True)
        print("="*70, flush=True)
        print(f"Model: {embedding_model}", flush=True)
        print("", flush=True)
        
        # This line may take time on first run
        self.embedding_model = SentenceTransformer(embedding_model)
        
        print("✅ Embedding model loaded successfully!", flush=True)
        print("="*70, flush=True)
        print("", flush=True)
        
        # 2. Initialize LanceDB (FREE - local database)
        print("🗄️ Connecting to LanceDB...")
        db_path = Path(__file__).parent / "lancedb"
        self.db = lancedb.connect(str(db_path))
        print(f"✓ LanceDB connected successfully")
        print("", flush=True)
        
        # 3. Setup Groq LLM (Fast and FREE tier)
        if self.groq_api_key and self.groq_api_key != "your_groq_api_key_here":
            self.groq_client = Groq(api_key=self.groq_api_key)
            print(f"🤖 Connected to Groq")
            print(f"   ✓ Model: {self.llm_model}")
        else:
            print("⚠️  Warning: No Groq API key configured!")
            print("Add to .env file: GROQ_API_KEY=your_groq_api_key_here")
            self.groq_client = None
        
        # 4. Load and index documents
        self.index_documents()
    
    def load_documents(self):
        """Load code files and documentation"""
        print("\n📂 Loading documents...")
        
        documents = []
        base_path = Path(__file__).parent.parent  # Go up to project root
        
        # Load documentation from rag_system/documents/
        docs_path = Path(__file__).parent / "documents"
        try:
            doc_loader = DirectoryLoader(
                str(docs_path),
                glob="**/*.md",
                loader_cls=TextLoader,
                silent_errors=True
            )
            doc_files = doc_loader.load()
            documents.extend(doc_files)
            print(f"   ✓ Loaded {len(doc_files)} documentation files from rag_system/documents/")
        except Exception as e:
            print(f"   ⚠️  Error loading documentation: {e}")
        
        # Load Python files from accounts/services/
        try:
            services_path = base_path / "accounts" / "services"
            if services_path.exists():
                code_loader = DirectoryLoader(
                    str(services_path),
                    glob="**/*.py",
                    loader_cls=TextLoader,
                    silent_errors=True
                )
                code_docs = code_loader.load()
                documents.extend(code_docs)
                print(f"   ✓ Loaded {len(code_docs)} Python files from accounts/services/")
        except Exception as e:
            print(f"   ⚠️  Error loading Python files: {e}")
        
        # Load README files from project root
        try:
            readme_loader = DirectoryLoader(
                str(base_path),
                glob="*.md",
                loader_cls=TextLoader,
                silent_errors=True
            )
            readme_docs = readme_loader.load()
            documents.extend(readme_docs)
            print(f"   ✓ Loaded {len(readme_docs)} README files")
        except Exception as e:
            print(f"   ⚠️  Error loading README files: {e}")
        
        # Load test file
        try:
            test_file = base_path / "test_refactoring.py"
            if test_file.exists():
                test_loader = TextLoader(str(test_file))
                test_doc = test_loader.load()
                documents.extend(test_doc)
                print(f"   ✓ Loaded test file")
        except Exception as e:
            print(f"   ⚠️  Error loading test file: {e}")
        
        print(f"📊 Total documents loaded: {len(documents)}")
        return documents
    
    def split_documents(self, documents):
        """Split documents into chunks"""
        print("✂️  Splitting documents into chunks...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        texts = text_splitter.split_documents(documents)
        print(f"   ✓ Created {len(texts)} text chunks")
        
        return texts
    
    def create_embeddings(self, texts):
        """Create embeddings for text chunks"""
        print("🔢 Creating embeddings...")
        
        data = []
        for i, doc in enumerate(texts):
            if (i + 1) % 10 == 0:
                print(f"   Processing chunk {i + 1}/{len(texts)}...")
            
            embedding = self.embedding_model.encode(doc.page_content).tolist()
            data.append({
                'id': i,
                'text': doc.page_content,
                'source': doc.metadata.get('source', 'unknown'),
                'vector': embedding
            })
        
        print(f"   ✓ Created embeddings for {len(data)} chunks")
        return data
    
    def index_documents(self):
        """Load, split, embed, and index documents in LanceDB"""
        try:
            # Try to load existing table
            self.table = self.db.open_table("erpnext_docs")
            print("✅ Loaded existing index from LanceDB\n")
        except:
            # Create new index
            print("🔨 Creating new index...")
            documents = self.load_documents()
            
            if not documents:
                print("❌ No documents found to index!")
                return
            
            texts = self.split_documents(documents)
            data = self.create_embeddings(texts)
            
            # Create LanceDB table
            self.table = self.db.create_table("erpnext_docs", data, mode="overwrite")
            print("✅ Index created successfully!\n")
    
    def search(self, query, top_k=3):
        """Search for relevant documents"""
        # Create embedding for query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search in LanceDB
        results = self.table.search(query_embedding).limit(top_k).to_list()
        
        return results
    
    def ask(self, question):
        """Ask a question and get AI-generated answer"""
        if not self.groq_client:
            return "❌ Error: No Groq API key configured.\n   Get one free at: https://console.groq.com/keys\n   Then add to .env file: GROQ_API_KEY=your_key"
        
        # 1. Search for relevant context
        results = self.search(question, top_k=3)
        
        if not results:
            return "❌ No relevant context found in the codebase."
        
        # 2. Combine retrieved context
        context = "\n\n".join([r['text'] for r in results])
        sources = [r['source'] for r in results]
        
        # 3. Create prompt for Groq
        prompt = f"""You are an expert software engineer analyzing an ERPNext refactoring project.

Answer the user's question based ONLY on the provided context. Be direct and focused.

CONTEXT FROM CODEBASE:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer ONLY what is asked in the question
2. Use ONLY information from the context that is directly relevant
3. If the context contains unrelated information, IGNORE it
4. Be clear, concise, and focused on the specific question
5. If the context doesn't fully answer the question, state what information is available
6. Do NOT include meta-notes like "Note that the context does not explicitly..." or "can be inferred" - just provide the direct answer

Answer:"""

        # 4. Get answer from Groq (Very fast!)
        
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.llm_model,
                temperature=0.3,  # Lower = more focused answers
                max_tokens=1024,
            )
            
            answer = chat_completion.choices[0].message.content
            
            # 5. Show sources
            print(f"\n📚 Sources used:")
            for source in set(sources):
                # Show relative path
                rel_path = source.replace(str(Path(__file__).parent.parent), '').lstrip('\\//')
                print(f"   • {rel_path}")
            
            return answer
            
        except Exception as e:
            return f"❌ Error getting answer from Groq: {str(e)}"


def main():
    """Main function to run RAG system"""
    
    print("="*70)
    print("ERPNext RAG System - AI-Powered Code Query")
    print("="*70)
    print()
    
    # Initialize RAG system (will load from .env)
    rag = ERPNextRAG()
    
    if not rag.groq_client:
        return
    
    print("\n" + "="*70)
    print("Interactive Mode")
    print("="*70)
    print("Type your questions (or 'quit' to exit)")
    print()
    
    while True:
        question = input("\n💬 Your question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not question:
            continue
        
        answer = rag.ask(question)
        print(f"\n✅ Answer:\n{answer}")


if __name__ == "__main__":
    main()
