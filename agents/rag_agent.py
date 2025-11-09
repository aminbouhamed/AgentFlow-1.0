from typing import List, Dict
from pydantic import BaseModel, Field
from tools.vector_store import VectorStore

class RetrievedDocument(BaseModel):
    """Single retrieved document"""
    title: str
    content: str
    relevance_score: float
    category: str
    why_relevant: str = Field(
        description="Brief explanation of why this document is relevant"
    )

class RAGResults(BaseModel):
    """Structured RAG retrieval results"""
    query: str
    documents: List[RetrievedDocument]
    total_found: int
    retrieval_strategy: str = Field(
        description="Which search strategy was used"
    )

class RAGAgent:
    """Agent responsible for knowledge retrieval"""
    
    def __init__(self):
        self.vector_store = VectorStore()
    
    def retrieve(
        self,
        query: str,
        industry: str = None,
        requirements: List[str] = None,
        limit: int = 3
    ) -> RAGResults:
        """
        Retrieve relevant documents from knowledge base
        
        Args:
            query: Main search query
            industry: Industry to filter by (optional)
            requirements: List of specific requirements for keyword boosting
            limit: Number of documents to retrieve
            
        Returns:
            RAGResults with relevant documents
        """
        
        print(f" RAG Agent: Searching for '{query}'",flush=True)
        
        # Build enhanced query
        enhanced_query = query
        if industry:
            enhanced_query = f"{query} {industry}"
        
        # search strategy
        if requirements and len(requirements) > 0:
            
            keywords = requirements + ([industry] if industry else [])
            results = self.vector_store.hybrid_search(
                query=enhanced_query,
                keywords=keywords,
                limit=limit
            )
            strategy = "hybrid_search_with_keywords"
        else:
            # Use semantic search only
            results = self.vector_store.search(
                query=enhanced_query,
                limit=limit
            )
            strategy = "semantic_search"
        

        documents = []
        for result in results:
            doc = RetrievedDocument(
                title=result.get('title', 'Untitled'),
                content=result.get('content', ''),
                relevance_score=result.get('score', 0.0),
                category=result.get('category', 'unknown'),
                why_relevant=self._explain_relevance(result, query, requirements)
            )
            documents.append(doc)
        
        print(f"✅ RAG Agent: Found {len(documents)} relevant documents",flush=True)
        
        return RAGResults(
            query=query,
            documents=documents,
            total_found=len(documents),
            retrieval_strategy=strategy
        )
    
    def _explain_relevance(
        self,
        document: Dict,
        query: str,
        requirements: List[str]
    ) -> str:
        """Generate brief explanation of why document is relevant"""
        
        reasons = []
        
        
        category = document.get('category', '')
        if category == 'case_study':
            reasons.append("similar past project")
        elif category == 'product':
            reasons.append("relevant product offering")
        
        
        if document.get('industry'):
            reasons.append(f"same industry ({document['industry']})")
        
        
        if requirements:
            matching_tags = [
                tag for tag in document.get('tags', []) or []
                if any(req.lower() in str(tag).lower() for req in requirements)
            ]
            if matching_tags:
                reasons.append(f"matches requirements: {', '.join(matching_tags[:2])}")
        
        if not reasons:
            return "High semantic similarity to query"
        
        return " | ".join(reasons)


# Test function
if __name__ == "__main__":
    rag = RAGAgent()
    
    print("="*80)
    print(" Testing RAG Agent with Titan Embeddings")
    print("="*80)
    
    # Test case 1: Quality control query
    print("\nTest Case 1: Quality Control")
    results = rag.retrieve(
        query="knowing more about your AI solutions",
        industry="automotive",
        requirements=["quality control", "defect detection", "real-time", "your previous work"],
        limit=3
    )
    
    print(f"\nQuery: {results.query}")
    print(f"Strategy: {results.retrieval_strategy}")
    print(f"Found: {results.total_found} documents\n")
    
    for i, doc in enumerate(results.documents, 1):
        print(f"{i}. {doc.title}")
        print(f"   Score: {doc.relevance_score:.3f}")
        print(f"   Category: {doc.category}")
        print(f"   Why relevant: {doc.why_relevant}")
        print(f"   Snippet: {doc.content[:150]}...")
        print()
    
    # Test case 2: E-commerce query
    print("\n" + "="*80)
    print(" Test Case 2: E-commerce Recommendations")
    print("="*80)
    
    results = rag.retrieve(
        query="recommendation system for online shopping",
        industry="e-commerce",
        requirements=["personalization", "real-time"],
        limit=2
    )
    
    print(f"\nFound: {results.total_found} documents\n")
    for i, doc in enumerate(results.documents, 1):
        print(f"{i}. {doc.title} (score: {doc.relevance_score:.3f})")
        print(f"   {doc.why_relevant}")