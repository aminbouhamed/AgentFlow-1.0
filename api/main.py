from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import os
import time
from pathlib import Path
from datetime import datetime

from agents.orchestrator import AgentOrchestrator
from monitoring.metrics import MetricsCollector
from api.database import HistoryDB  # Importation of  the history database

# Initialize FastAPI
app = FastAPI(
    title="AgentFlow API",
    description="Multi-Agent AI System for Business Email Processing",
    version="1.0.0"
)

# CORS middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables (initialized on startup)
orchestrator = None
metrics_collector = None
history_db = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator and services on startup"""
    global orchestrator, metrics_collector, history_db
    
    print(" AgentFlow starting up...")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"   AWS Region: {os.getenv('AWS_REGION', 'not set')}")
    print(f"   Qdrant URL: {os.getenv('QDRANT_URL', 'http://localhost:6333')}")
    
    # Wait for Qdrant to be ready 
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
    if "localhost" in qdrant_url or "127.0.0.1" in qdrant_url: 
        print(f" Waiting for Qdrant at {qdrant_url}...")
        
        # Retry logic for Qdrant connection
        max_retries = 10
        for i in range(max_retries):
            try:
                from qdrant_client import QdrantClient
                client = QdrantClient(url=qdrant_url)
                client.get_collections()  # Test connection
                print("✅ Qdrant is ready!")
                break
            except Exception as e:
                if i < max_retries - 1:
                    print(f" Qdrant not ready yet (attempt {i+1}/{max_retries}), waiting 3s...")
                    time.sleep(3)
                else:
                    print(f"⚠️  Could not connect to Qdrant after {max_retries} attempts")
                    print(f"   Error: {e}")
                    print("   Continuing with in-memory fallback...")
    else:
        print(f"  Using Qdrant Cloud at {qdrant_url}")
        if not qdrant_api_key:
            print("⚠️  Warning: QDRANT_API_KEY not set for cloud connection!")
        else:
            print("✅ Qdrant Cloud credentials configured")

            # test connection
            try:
                from qdrant_client import QdrantClient
                client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
                collections = client.get_collections()
                print(f"✅ Successfully connected to Qdrant Cloud ({len(collections.collections)} collections)")
            except Exception as e:
                print(f"⚠️  Warning: Could not verify Qdrant Cloud connection: {e}")
                print("   Will retry during initialization...")
    
    # Initialize history database
    try:
        history_db = HistoryDB()
        print("✅ History database initialized")
    except Exception as e:
        print(f"⚠️  History database initialization failed: {e}")
        history_db = None
    
    # Initialize metrics collector
    try:
        metrics_collector = MetricsCollector()
        print("✅ Metrics collector initialized")
    except Exception as e:
        print(f"⚠️  Metrics collector initialization failed: {e}")
        metrics_collector = None
    
    # Initialize orchestrator
    try:
        orchestrator = AgentOrchestrator()
        print("✅ Orchestrator initialized")
    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        raise
    
    # Initialize knowledge base
    try:
        print(" Initializing knowledge base...")
        from tools.vector_store import initialize_knowledge_base
        initialize_knowledge_base()
        print("✅ Knowledge base initialized")
    except Exception as e:
        print(f"⚠️  Knowledge base initialization warning: {e}")
        print("   System will continue with limited context")
    
    print(" AgentFlow ready to process emails!")

# Serve static files if available
static_dir = Path("api/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    print(f" Serving static files from {static_dir}")

# Request/Response models
class EmailRequest(BaseModel):
    """Request to process an email"""
    email_text: str = Field(..., description="Complete email content")
    priority: Optional[str] = Field("normal", description="Priority level")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata")

class EmailResponse(BaseModel):
    """Response with processed email"""
    request_id: str
    status: str
    decision: str
    confidence: float
    response_subject: str
    response_body: str
    processing_time: float
    quality_approved: bool
    issues_found: int
    metadata: Dict

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    agents_loaded: int
    environment: Optional[str] = None
    qdrant_connected: Optional[bool] = None

# Routes

@app.get("/")
async def root():
    """Root endpoint - serve static page if available, otherwise JSON"""
    static_index = Path("api/static/index.html")
    if static_index.exists():
        return FileResponse(static_index)
    
    return {
        "service": "AgentFlow",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "history": "/history",
        "message": "Multi-Agent AI System for Business Email Processing"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    
    # Check Qdrant connection
    qdrant_connected = False
    try:
        from tools.vector_store import VectorStore
        vs = VectorStore()
        qdrant_connected = True
    except:
        qdrant_connected = False
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        agents_loaded=6,
        environment=os.getenv("ENVIRONMENT", "development"),
        qdrant_connected=qdrant_connected
    )

@app.post("/process", response_model=EmailResponse)
async def process_email(
    request: EmailRequest,
    background_tasks: BackgroundTasks
):
    """
    Process an email through the agent workflow
    
    Args:
        request: Email to process
        
    Returns:
        Processed email with agent decision
    """
    
    import uuid
    
    # Check if orchestrator is initialized
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready. Orchestrator not initialized."
        )
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Process email
        result = orchestrator.process_email(request.email_text)
        
        processing_time = time.time() - start_time
        
        # Check for errors
        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Processing error: {result['error']}"
            )
        
        # Build response
        response = EmailResponse(
            request_id=request_id,
            status="success",
            decision=result["decision"].action,
            confidence=result["quality_check"].confidence,
            response_subject=result["response"].subject,
            response_body=result["response"].full_email,
            processing_time=processing_time,
            quality_approved=result["quality_check"].approved,
            issues_found=len(result["quality_check"].issues_found),
            metadata={
                "intent": result["classification"].intent,
                "company": result["classification"].company_name,
                "urgency": result["classification"].urgency,
                "priority": result["decision"].priority,
                "rag_documents_used": len(result["rag_results"].documents)
            }
        )
        
        # Save to history database 
        if history_db:
            history_entry = {
                'request_id': request_id,
                'email_text': request.email_text,
                'decision': response.decision,
                'confidence': response.confidence,
                'response_subject': response.response_subject,
                'response_body': response.response_body,
                'processing_time': response.processing_time,
                'quality_approved': response.quality_approved,
                'metadata': response.metadata
            }
            background_tasks.add_task(history_db.add_entry, history_entry)
        
        # Log metrics in background (if collector is healthy and working rightly)
        if metrics_collector:
            background_tasks.add_task(metrics_collector.log_request, result)
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing request {request_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

# History endpoints
@app.get("/history", response_model=List[Dict])
async def get_history(limit: int = 100):
    """Get processing history"""
    if history_db is None:
        raise HTTPException(
            status_code=503,
            detail="History database not available"
        )
    
    try:
        return history_db.get_all_entries(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching history: {str(e)}"
        )

@app.get("/history/{request_id}", response_model=Dict)
async def get_history_entry(request_id: str):
    """Get a specific history entry"""
    if history_db is None:
        raise HTTPException(
            status_code=503,
            detail="History database not available"
        )
    
    entry = history_db.get_entry(request_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@app.delete("/history/{request_id}")
async def delete_history_entry(request_id: str):
    """Delete a history entry"""
    if history_db is None:
        raise HTTPException(
            status_code=503,
            detail="History database not available"
        )
    
    success = history_db.delete_entry(request_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found or could not be deleted")
    return {"message": "Entry deleted successfully"}

@app.delete("/history")
async def clear_history():
    """Clear all history"""
    if history_db is None:
        raise HTTPException(
            status_code=503,
            detail="History database not available"
        )
    
    success = history_db.clear_all()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear history")
    return {"message": "History cleared successfully"}

# Statistics endpoint
@app.get("/stats", response_model=Dict)
async def get_stats():
    """Get processing statistics from history"""
    if history_db is None:
        raise HTTPException(
            status_code=503,
            detail="History database not available"
        )
    
    try:
        return history_db.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching statistics: {str(e)}"
        )

@app.get("/metrics", response_model=Dict)
async def get_metrics():
    """Get system metrics"""
    if metrics_collector is None:
        return {"error": "Metrics collector not available"}
    
    stats = metrics_collector.get_summary_stats()
    return stats

@app.get("/metrics/dashboard")
async def metrics_dashboard():
    """HTML dashboard for metrics"""
    if metrics_collector is None:
        return HTMLResponse(content="<h1>Metrics collector not available</h1>")
    
    stats = metrics_collector.get_summary_stats()
    
    if "error" in stats:
        return HTMLResponse(content=f"<h1>Error: {stats['error']}</h1>")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgentFlow Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{ 
                max-width: 1200px;
                margin: 0 auto;
                background: white; 
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{ 
                color: #667eea; 
                margin-bottom: 30px;
                font-size: 2.5rem;
            }}
            h2 {{ 
                color: #333; 
                margin: 30px 0 20px 0;
                font-size: 1.5rem;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric {{ 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                color: white;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
            .metric-label {{ 
                font-weight: 600;
                font-size: 0.9rem;
                opacity: 0.9;
                margin-bottom: 10px;
            }}
            .metric-value {{ 
                font-size: 2.5rem;
                font-weight: bold;
            }}
            .decision-breakdown {{ 
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .decision-card {{ 
                padding: 20px;
                background: #f0f7ff;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }}
            .decision-card .metric-label {{
                color: #666;
                font-size: 0.9rem;
            }}
            .decision-card .metric-value {{
                color: #333;
                font-size: 2rem;
            }}
            .decision-card .percentage {{
                color: #667eea;
                font-weight: 600;
                margin-top: 5px;
            }}
            .refresh-btn {{
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
            .refresh-btn:hover {{
                background: #5568d3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AgentFlow Dashboard</h1>
            
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Total Requests</div>
                    <div class="metric-value">{stats.get('total_requests', 0)}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value">{stats.get('success_rate', 0):.1f}%</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Autonomous Handling</div>
                    <div class="metric-value">{stats.get('autonomous_handling_rate', 0):.1f}%</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value">{stats.get('avg_processing_time', 0):.1f}s</div>
                </div>
            </div>
            
            <h2>📊 Decision Breakdown</h2>
            <div class="decision-breakdown">
    """
    
    decision_breakdown = stats.get('decision_breakdown', {})
    successful = stats.get('successful', 1)  
    
    for decision, count in decision_breakdown.items():
        percentage = (count / successful * 100) if successful > 0 else 0
        html += f"""
                <div class="decision-card">
                    <div class="metric-label">{decision.replace('_', ' ').title()}</div>
                    <div class="metric-value">{count}</div>
                    <div class="percentage">{percentage:.1f}%</div>
                </div>
        """
    
    html += """
            </div>
            
            <a href="/metrics/dashboard" class="refresh-btn">🔄 Refresh</a>
            <a href="/docs" class="refresh-btn">📚 API Docs</a>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

#shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print(" AgentFlow shutting down...")
    

# local test
#if __name__ == "__main__":
#    import uvicorn
#    port = int(os.getenv("PORT", 8000))
#    uvicorn.run(
#        "api.main:app",
#        host="0.0.0.0",
#        port=port,
#        reload=True
#    )