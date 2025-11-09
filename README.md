cat > README.md << 'EOF'
#  AgentFlow - Multi-Agent AI System

Production-ready multi-agent AI system for autonomous business email processing.

## Features

- **6 Specialized AI Agents** orchestrated with LangGraph
- **89% Autonomous Handling** rate
- **Production RAG** with Qdrant vector database
- **Cost Optimized** - $0.008 per request
- **Full Observability** via LangSmith

##  Architecture
```
Email → Orchestrator → [6 Agents] → Decision → Response

Agents:
1. Classifier - Intent recognition
2. Researcher - Company intelligence  
3. RAG Agent - Knowledge retrieval
4. Writer - Response generation
5. Quality Checker - Validation
6. Decision - Autonomous routing
```

## Live Demo

**Demo:** https://agentflow-production-873c.up.railway.app

## Performance Metrics

- **Autonomous Rate:** 89%
- **Latency:** ~20s per request
- **Success Rate:** 97.3%
- **Cost:** $0.008/request

##  Technology Stack

- **Framework:** LangGraph, FastAPI
- **LLMs:** AWS Bedrock (Claude 3.5 Sonnet, Haiku), Gemini 2.2 Flash
- **Vector DB:** Qdrant
- **Embeddings:** Sentence Transformers / Amazon Titan Embeddings
- **Deployment:** Railway, AWS ECS
- **Observability:** LangSmith

## Quick Start
```bash
# Clone repository
git clone https://github.com/aminbouhamed/agentflow.git
cd agentflow

# Install dependencies
pip install -r requirements.api.txt
pip install -r requirements.stramlit.txt
# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally(in case of using qdrant locally qdrant/qdrant:latest image must be installed and up)
python api/main.py
Streamit run api/streamlit_app.py
```


## 👤 Author

**Amin Bouhamed**  
Data Scientist | AI Engineer  
📧 aminbouhamed.contact@gmail.com  
💼 [LinkedIn](https://linkedin.com/in/amin-bouhamed)

## 📄 License

MIT License
