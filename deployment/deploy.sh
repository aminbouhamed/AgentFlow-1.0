#!/bin/bash

# AgentFlow Deployment Script it can be used ti deploy to different platforms (railway, render, aws ecs, docker-compose)


set -e


GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' 

echo -e "${BLUE}🚀 AgentFlow Deployment Script${NC}"
echo "=================================="

if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Environment not specified${NC}"
    echo "Usage: ./deploy.sh [platform]"
    echo "Platforms: docker, aws, railway, render"
    exit 1
fi

PLATFORM=$1

case $PLATFORM in
    docker)
        echo -e "${GREEN}📦 Deploying with Docker Compose...${NC}"
        docker-compose build
        docker-compose up -d
        echo -e "${GREEN}✅ Deployed successfully!${NC}"
        echo "API: http://localhost:8000"
        echo "UI: http://localhost:8501"
        ;;
    
    aws)
        echo -e "${GREEN}☁️ Deploying to AWS ECS...${NC}"
        
        # Build and push Docker image
        echo "Building Docker image..."
        docker build -t agentflow:latest .
        
        # Tag and push to ECR
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        AWS_REGION=${AWS_REGION:-us-east-1}
        ECR_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agentflow-prod"
        
        echo "Logging into ECR..."
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO
        
        echo "Pushing to ECR..."
        docker tag agentflow:latest $ECR_REPO:latest
        docker push $ECR_REPO:latest
        
        echo -e "${GREEN}✅ Image pushed to ECR!${NC}"
        echo "Next: Deploy ECS task definition"
        ;;
    
    railway)
        echo -e "${GREEN}🚂 Deploying to Railway...${NC}"
        
        if ! command -v railway &> /dev/null; then
            echo -e "${RED}❌ Railway CLI not installed${NC}"
            echo "Install: npm i -g @railway/cli"
            exit 1
        fi
        
        railway up
        echo -e "${GREEN}✅ Deployed to Railway!${NC}"
        ;;
    
    render)
        echo -e "${GREEN}🎨 Deploying to Render...${NC}"
        echo "Visit https://dashboard.render.com to deploy"
        echo "Use the render.yaml configuration file"
        ;;
    
    *)
        echo -e "${RED}❌ Unknown platform: $PLATFORM${NC}"
        echo "Available platforms: docker, aws, railway, render"
        exit 1
        ;;
esac
