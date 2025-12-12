"""
RAG Service - LangGraph Documentation Chatbot
Enhanced version with better scraping and verification
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
import time
import re

# Load environment variables
load_dotenv()

# Configure LlamaIndex
Settings.llm = OpenAI(model="gpt-4", temperature=0.7)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")


class RAGService:
    """RAG service for LangGraph documentation"""
    
    def __init__(self, collection_name="langraph_docs"):
        print("🚀 Initializing RAG Service...")
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(collection_name)
        
        # Setup vector store
        vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Initialize index
        self.index = None
        
        # Track scraped pages
        self.scraped_pages = []
        
        # Try to load existing index
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store,
                storage_context=self.storage_context
            )
            print("✅ Loaded existing index from ChromaDB")
        except:
            print("ℹ️ No existing index found. Will create on first ingestion.")
        
        print("✅ RAG Service initialized")
    
    def scrape_langchain_docs(self, start_url: str, max_pages: int = 30) -> List[Document]:
        """
        Scrape LangChain documentation (improved for docs.langchain.com structure)
        
        Args:
            start_url: Starting URL (e.g., https://docs.langchain.com/oss/python/langgraph/overview)
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of Document objects
        """
        print(f"\n🌐 Starting to scrape from: {start_url}")
        print(f"📊 Max pages to scrape: {max_pages}")
        
        documents = []
        visited_urls = set()
        urls_to_visit = [start_url]
        
        # Get base domain for filtering
        parsed_start = urlparse(start_url)
        base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"
        
        # Only follow links within the LangGraph section
        langgraph_path_pattern = re.compile(r'/langgraph/')
        
        page_count = 0
        
        while urls_to_visit and page_count < max_pages:
            url = urls_to_visit.pop(0)
            
            # Skip if already visited
            if url in visited_urls:
                continue
            
            visited_urls.add(url)
            page_count += 1
            
            try:
                print(f"\n📄 [{page_count}/{max_pages}] Scraping: {url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, timeout=15, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple content selectors (LangChain docs structure)
                # Check for various possible containers
                main_content = (
                    soup.find('article') or 
                    soup.find('main') or 
                    soup.find('div', class_='content') or
                    soup.find('div', {'role': 'main'}) or
                    soup.find('div', class_='markdown') or
                    soup.find('div', id='content') or
                    soup.find('div', class_='docs-content') or
                    soup.find('div', class_='page-content') or
                    soup.find('section', class_='content')
                )
                
                # If still no content found, try to find the largest div with text
                if not main_content:
                    print(f"  ⚠️ Standard selectors failed, trying fallback...")
                    all_divs = soup.find_all('div')
                    if all_divs:
                        # Find div with most text content
                        main_content = max(all_divs, key=lambda d: len(d.get_text(strip=True)))
                        if len(main_content.get_text(strip=True)) < 500:
                            main_content = None
                
                if main_content:
                    # Remove unwanted elements
                    for tag in main_content.find_all(['nav', 'header', 'footer', 'script', 'style', 'aside', 'button']):
                        tag.decompose()
                    
                    # Extract text
                    text = main_content.get_text(separator='\n', strip=True)
                    
                    # Clean up text
                    text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive newlines
                    text = text.strip()
                    
                    # Only add if there's substantial content
                    if len(text) > 300:
                        # Get title
                        title = soup.title.string if soup.title else url.split('/')[-1]
                        title = title.replace(' | 🦜️🔗 LangChain', '').strip()
                        
                        doc = Document(
                            text=text,
                            metadata={
                                "source": url,
                                "title": title,
                                "page_number": page_count
                            }
                        )
                        documents.append(doc)
                        
                        # Track for reporting
                        self.scraped_pages.append({
                            "url": url,
                            "title": title,
                            "length": len(text),
                            "page_number": page_count
                        })
                        
                        print(f"  ✅ Added: {title}")
                        print(f"  📏 Length: {len(text)} chars")
                        
                        # Find links to other LangGraph pages
                        if page_count < max_pages:
                            for link in main_content.find_all('a', href=True):
                                href = link['href']
                                
                                # Skip anchors and external links
                                if href.startswith('#') or href.startswith('http') and not href.startswith(base_domain):
                                    continue
                                
                                # Construct full URL
                                full_url = urljoin(url, href)
                                
                                # Only follow LangGraph-related links
                                if (full_url.startswith(base_domain) and 
                                    langgraph_path_pattern.search(full_url) and
                                    full_url not in visited_urls and
                                    full_url not in urls_to_visit):
                                    urls_to_visit.append(full_url)
                                    print(f"  🔗 Found link: {full_url.split('/')[-1]}")
                    else:
                        print(f"  ⚠️ Skipped: Content too short ({len(text)} chars)")
                else:
                    print(f"  ❌ No main content found")
                
                # Be nice to the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error scraping {url}: {str(e)}")
                continue
        
        print(f"\n✅ Scraping complete!")
        print(f"📊 Total pages scraped: {len(documents)}")
        print(f"📈 Total characters: {sum(len(doc.text) for doc in documents)}")
        
        return documents
    
    def ingest_documents(self, documents: Optional[List[Document]] = None, url: Optional[str] = None, max_pages: int = 30) -> Dict[str, Any]:
        """
        Ingest documents into the RAG system
        
        Args:
            documents: List of Document objects (if already scraped)
            url: URL to scrape (if documents not provided)
            max_pages: Maximum pages to scrape
            
        Returns:
            Result dictionary
        """
        try:
            # Reset scraped pages tracking
            self.scraped_pages = []
            
            # Scrape if URL provided
            if url and not documents:
                print(f"🌐 Scraping from URL: {url}")
                documents = self.scrape_langchain_docs(url, max_pages=max_pages)
            
            if not documents:
                return {
                    "status": "error",
                    "message": "No documents provided or scraped",
                    "pages_scraped": []
                }
            
            print(f"\n📚 Ingesting {len(documents)} documents...")
            
            # Create or update index
            if self.index is None:
                print("Creating new index...")
                self.index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=self.storage_context,
                    show_progress=True
                )
            else:
                print("Adding to existing index...")
                for doc in documents:
                    self.index.insert(doc)
            
            print("✅ Documents ingested successfully")
            
            return {
                "status": "success",
                "message": f"Successfully ingested {len(documents)} documents",
                "document_count": len(documents),
                "pages_scraped": self.scraped_pages,
                "total_characters": sum(len(doc.text) for doc in documents)
            }
            
        except Exception as e:
            error_msg = f"Error during ingestion: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": error_msg,
                "pages_scraped": self.scraped_pages
            }
    
    def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            question: User's question
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Answer with sources
        """
        print(f"\n💬 Query: {question}")
        
        try:
            if self.index is None:
                return {
                    "status": "error",
                    "answer": "No documents have been ingested yet. Please ingest documents first.",
                    "sources": []
                }
            
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="compact"
            )
            
            # Execute query
            response = query_engine.query(question)
            
            # Extract sources
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    sources.append({
                        "text": node.text[:300] + "..." if len(node.text) > 300 else node.text,
                        "score": node.score if hasattr(node, 'score') else None,
                        "metadata": node.metadata if hasattr(node, 'metadata') else {}
                    })
            
            print(f"✅ Generated answer with {len(sources)} sources")
            
            return {
                "status": "success",
                "answer": str(response),
                "sources": sources
            }
            
        except Exception as e:
            error_msg = f"Error during query: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "answer": error_msg,
                "sources": []
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested documents"""
        try:
            if self.index is None:
                return {
                    "status": "no_index",
                    "message": "No documents ingested yet"
                }
            
            # Get collection stats
            collection_count = self.collection.count()
            
            return {
                "status": "success",
                "document_count": len(self.scraped_pages),
                "vector_count": collection_count,
                "pages": self.scraped_pages
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


# Flask API
app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js

# Initialize RAG service
print("=" * 60)
print("🚀 Starting LangGraph Documentation RAG Service")
print("=" * 60)
rag_service = RAGService()


@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "service": "LangGraph Documentation RAG Service",
        "status": "running",
        "endpoints": {
            "/health": "GET - Health check",
            "/ingest": "POST - Ingest documents",
            "/query": "POST - Query the RAG system",
            "/stats": "GET - Get ingestion statistics"
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "index_ready": rag_service.index is not None,
        "documents_ingested": len(rag_service.scraped_pages)
    })


@app.route('/ingest', methods=['POST'])
def ingest():
    """
    Ingest documents endpoint
    
    Request body:
    {
        "url": "https://docs.langchain.com/oss/python/langgraph/overview",
        "max_pages": 30  // Optional: number of pages to scrape
    }
    """
    data = request.json
    
    url = data.get('url', 'https://docs.langchain.com/oss/python/langgraph/overview')
    max_pages = data.get('max_pages', 30)
    
    print(f"\n📥 Ingestion request received:")
    print(f"  URL: {url}")
    print(f"  Max pages: {max_pages}")
    
    result = rag_service.ingest_documents(url=url, max_pages=max_pages)
    
    status_code = 200 if result['status'] == 'success' else 400
    return jsonify(result), status_code


@app.route('/query', methods=['POST'])
def query():
    """
    Query endpoint
    
    Request body:
    {
        "question": "What is LangGraph?",
        "top_k": 3  // Optional: number of sources
    }
    """
    data = request.json
    
    if not data or 'question' not in data:
        return jsonify({
            "status": "error",
            "answer": "Missing 'question' in request body",
            "sources": []
        }), 400
    
    question = data['question']
    top_k = data.get('top_k', 3)
    
    result = rag_service.query(question, top_k)
    
    status_code = 200 if result['status'] == 'success' else 400
    return jsonify(result), status_code


@app.route('/stats', methods=['GET'])
def stats():
    """
    Get statistics about ingested documents
    """
    result = rag_service.get_stats()
    return jsonify(result)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("✅ RAG Service Ready!")
    print("📍 Running on: http://localhost:5001")
    print("=" * 60)
    print("\n💡 Tip: Use correct LangGraph docs URL:")
    print("   https://docs.langchain.com/oss/python/langgraph/overview")
    print("\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)