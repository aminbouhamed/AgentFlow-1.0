#!/bin/bash

echo "Initializing AgentFlow system..."


if [ ! -f .env ]; then
    echo ".env file not found! Please create one based on .env.example"
    exit 1
fi 


export $(cat .env | xargs)


echo "Starting Docker containers..."
docker-compose up -d


echo "waiting for services to initialize..."
sleep 10


echo "Checking Qdrant"
until curl -s http://localhost:6333 > /dev/null; do
    echo "Qdrant is not up yet - waiting..."
    sleep 2
done
echo "Qdrant is Ready "


echo " Initializing knowledge base..."
docker-compose exec api python -c "from tools.vector_store import initialize_knowledge_base; initialize_knowledge_base()"


echo " Checking API..."
until curl -s http://localhost:8000/health > /dev/null; do
    echo "Waiting for API..."
    sleep 2
done
echo " API is ready"



echo ""
echo "="*80
echo "AgentFlow System Initialized!"
echo "="*80
echo ""
echo " Services:"
echo "   API:        http://localhost:8000"
echo "   Docs:       http://localhost:8000/docs"
echo "   Streamlit:  http://localhost:8501"
echo "   Qdrant:     http://localhost:6333/dashboard"
echo ""
echo " Check logs: docker-compose logs -f"
echo " Stop system: docker-compose down"
echo ""