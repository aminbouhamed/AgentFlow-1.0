# tools/vector_store.py

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct
import json
from typing import List, Dict
import uuid
import os
import boto3
from dotenv import load_dotenv

load_dotenv()  
class VectorStore:
    """Vector store using Qdrant with AWS Titan Embeddings"""
    
    def __init__(self, collection_name: str = "knowledge_base"):
        # Qdrant setup
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
        
        print(f" Connecting to Qdrant at: {qdrant_url}")
        
        try:
            if qdrant_api_key:
                self.client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    timeout=60
                )
                print("✅ Connected to Qdrant Cloud")
            else:
                self.client = QdrantClient(url=qdrant_url, timeout=60)
                print("✅ Connected to Qdrant")
        except Exception as e:
            print(f"❌ Qdrant connection failed: {e}")
            print("⚠️  Falling back to in-memory mode")
            self.client = QdrantClient(":memory:")
        
        self.collection_name = collection_name
        
        # AWS Bedrock setup for Titan Embeddings
        try:
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'none'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            print("✅ AWS Bedrock client initialized for Titan Embeddings")
        except Exception as e:
            print(f"⚠️  Bedrock client initialization warning: {e}")
            self.bedrock_runtime = None
        
        # Titan Embeddings V2 dimension
        self.embedding_dim = 1024  # Titan V2 uses 1024 dimensions
        
        self._create_collection()
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embeddings using AWS Titan Embeddings V2
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.bedrock_runtime:
            print("⚠️  Bedrock runtime not available, returning zero vector")
            return [0.0] * self.embedding_dim
        
        try:
            # Titan has max input length of 8000 characters
            text = text[:8000]
            
            # Prepare request for Titan Embeddings V2
            request_body = json.dumps({
                "inputText": text
            })
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=request_body,
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding')
            
            if not embedding:
                raise ValueError("No embedding returned from Titan")
            
            return embedding
            
        except Exception as e:
            print(f"❌ Error getting Titan embedding: {e}")
            # Fallback: return zero vector
            return [0.0] * self.embedding_dim
    
    def _create_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created collection: {self.collection_name}")
            else:
                print(f"✅ Collection already exists: {self.collection_name}")
        except Exception as e:
            print(f"⚠️  Could not create collection: {e}")
    
    def add_documents(self, documents: List[Dict]):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with document data
        """
        points = []
        
        for doc in documents:
            # Combine title and content for embedding
            text_to_embed = f"{doc.get('title', '')}\n\n{doc.get('content', '')}"
            
            # Get embedding using Titan
            embedding = self._get_embedding(text_to_embed)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "doc_id": doc.get('id'),
                    "title": doc.get('title', ''),
                    "content": doc.get('content', ''),
                    "category": doc.get('category', ''),
                    "industry": doc.get('industry', ''),
                    "tags": doc.get('tags', []),
                    "year": doc.get('year', 2024)
                }
            )
            points.append(point)
        
        if points:
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                print(f"✅ Added {len(points)} documents to vector store")
            except Exception as e:
                print(f"❌ Error adding documents: {e}")
    
    def search(self, 
               query: str, 
               limit: int = 5,
               filter_conditions: Dict = None) -> List[Dict]:
        """
        Semantic search in the vector store.
        
        Args:
            query: Search query
            limit: Number of results to return
            filter_conditions: Optional filter conditions
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Get query embedding using Titan
            query_embedding = self._get_embedding(query)
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=filter_conditions
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "score": hit.score,
                    "doc_id": hit.payload.get('doc_id'),
                    "title": hit.payload.get('title'),
                    "content": hit.payload.get('content'),
                    "category": hit.payload.get('category'),
                    "industry": hit.payload.get('industry'),
                    "tags": hit.payload.get('tags')
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        keywords: List[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Hybrid search combining semantic and keyword matching.
        
        Args:
            query: Search query
            keywords: Keywords to boost scores
            limit: Number of results to return
            
        Returns:
            List of matching documents with boosted scores
        """
        # Get semantic search results (fetch more to re-rank)
        results = self.search(query, limit=limit * 2)
        
        # Boost scores based on keyword matches
        if keywords:
            for result in results:
                # Making keyword check safer
                content_lower = str(result.get('content', '')).lower()
                tags_lower = [str(tag).lower() for tag in result.get('tags', []) or []]
                
                keyword_matches = sum(
                    1 for kw in keywords 
                    if kw.lower() in content_lower or kw.lower() in tags_lower
                )
                # Boost score based on keyword matches
                result['score'] = result['score'] * (1 + 0.2 * keyword_matches)
        
        # Re-sort and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]


def initialize_knowledge_base():
    """Load all documents into vector store, ONLY IF IT'S EMPTY."""
    
    print(" Initializing knowledge base with AWS Titan Embeddings...")
    
    vs = VectorStore()
    
    # Check if collection already has documents
    try:
        count_result = vs.client.count(collection_name=vs.collection_name, exact=True)
        if count_result.count > 0:
            print(f"✅ Knowledge base already contains {count_result.count} documents. Skipping initialization.")
            return vs
    except Exception as e:
        print(f"⚠️  Could not check collection count: {e}")
    
    print("📂 Knowledge base is empty. Initializing...")
    
    # Load documents from JSON files
    try:
        with open('data/knowledge_base/case_studies.json', 'r') as f:
            case_studies = json.load(f)
        print(f"✅ Loaded {len(case_studies)} case studies")
    except FileNotFoundError:
        print("⚠️  case_studies.json not found, skipping")
        case_studies = []
    
    try:
        with open('data/knowledge_base/company_info.json', 'r') as f:
            company_info = json.load(f)
        print(f"✅ Loaded {len(company_info)} company info documents")
    except FileNotFoundError:
        print("⚠️  company_info.json not found, skipping")
        company_info = []
    
    all_docs = case_studies + company_info
    
    if all_docs:
        vs.add_documents(all_docs)
        print(f"✅ Initialized knowledge base with {len(all_docs)} documents using Titan Embeddings")
    else:
        print("⚠️  No documents found to initialize")
    
    return vs


# For testing standalone
if __name__ == "__main__":
    vs = initialize_knowledge_base()
    
    print("\n" + "="*80)
    print(" Testing Semantic Search with Titan Embeddings")
    print("="*80)
    
    query = "do you provide modal recommendations"
    results = vs.search(query, limit=3)
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']} (score: {result['score']:.3f})")
            print(f"   Category: {result['category']}")
            print(f"   Snippet: {result['content'][:200]}...")
    else:
        print("No results found")
    
    print("\n" + "="*80)
    print(" Testing Hybrid Search")
    print("="*80)
    
    results = vs.hybrid_search(
        query="Who are you? What kind of company are you?",
        keywords=["automotive", "quality-control"],
        limit=3
    )
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']} (score: {result['score']:.3f})")
            print(f"   Tags: {result.get('tags', [])}")
    else:
        print("No results found")