#!/bin/bash
set -e

# Build the IPv6-enabled ChromaDB image
echo "Building ChromaDB with IPv6 support..."

# Option 1: Using the simple dual-stack approach (recommended to try first)
docker build -f Dockerfile.simple -t chromadb-ipv6:latest .

# To push to Docker Hub (replace 'yourusername' with your Docker Hub username):
# docker tag chromadb-ipv6:latest yourusername/chromadb-ipv6:latest
# docker push yourusername/chromadb-ipv6:latest

# To test locally:
echo "To test locally, run:"
echo "docker run -p 8000:8000 chromadb-ipv6:latest"

echo ""
echo "For Railway deployment:"
echo "1. Push to Docker Hub: docker push yourusername/chromadb-ipv6:latest"
echo "2. Update Railway to use: yourusername/chromadb-ipv6:latest"