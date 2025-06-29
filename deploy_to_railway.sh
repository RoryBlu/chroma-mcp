#!/bin/bash

# Railway Deployment Script for Chroma MCP
# This script will deploy your Chroma MCP with custom embedding support to Railway

set -e

echo "🚀 Deploying Chroma MCP to Railway"
echo "=================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check for Railway token
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "❌ RAILWAY_TOKEN environment variable not set!"
    echo ""
    echo "To deploy non-interactively, you need a Railway API token:"
    echo "1. Go to https://railway.app/account/tokens"
    echo "2. Create a new token"
    echo "3. Export it: export RAILWAY_TOKEN=your_token_here"
    echo "4. Run this script again"
    echo ""
    echo "Or run interactively with: railway login && railway up"
    exit 1
fi

echo "🔐 Using Railway token for authentication..."

# Initialize Railway project
echo "📋 Initializing Railway project..."
railway init

# Set environment variables based on your updated configuration
echo "🔧 Setting environment variables..."

# Chroma Configuration (HTTP client to external server)
# IMPORTANT: Check your Chroma server's private networking port in Railway dashboard!
# Go to chroma-gjdq service → Settings → Networking → Private Networking
# Use the port shown there, NOT necessarily 8000!
railway variables set CHROMA_CLIENT_TYPE=http
railway variables set CHROMA_HOST=chroma-gjdq.railway.internal
railway variables set CHROMA_PORT=8000  # CHANGE THIS to match Railway's private networking port!
railway variables set CHROMA_SSL=false

# Custom Embedding API Configuration
railway variables set EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
railway variables set EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
railway variables set EMBEDDING_DIMENSION=768

echo "✅ Environment variables set:"
echo "  - CHROMA_CLIENT_TYPE=http"
echo "  - CHROMA_HOST=chroma-gjdq.railway.internal"
echo "  - CHROMA_PORT=8000 (VERIFY THIS MATCHES RAILWAY's PRIVATE NETWORKING PORT!)"
echo "  - CHROMA_SSL=false"
echo "  - EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app"
echo "  - EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base"
echo "  - EMBEDDING_DIMENSION=768"

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "🎉 Deployment initiated!"
echo "Railway will now build and deploy your Chroma MCP service."
echo ""
echo "You can monitor the deployment progress at:"
echo "https://railway.app/dashboard"
echo ""
echo "Once deployed, your service will be available at a Railway-provided URL."