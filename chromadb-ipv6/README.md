# ChromaDB IPv6 Support for Railway

This directory contains Docker configurations to enable IPv6 support for ChromaDB on Railway.

## The Problem
Railway's private networking uses IPv6, but ChromaDB by default only binds to IPv4 (0.0.0.0). This causes "Connection refused" errors when services try to connect via Railway's internal network.

## Solution
We provide a custom Docker image that makes ChromaDB listen on both IPv4 and IPv6 interfaces.

## Quick Start

1. **Build the image locally:**
   ```bash
   cd chromadb-ipv6
   docker build -f Dockerfile.simple -t chromadb-ipv6:latest .
   ```

2. **Test locally:**
   ```bash
   docker run -p 8000:8000 chromadb-ipv6:latest
   ```

3. **Push to Docker Hub:**
   ```bash
   docker tag chromadb-ipv6:latest yourusername/chromadb-ipv6:latest
   docker login
   docker push yourusername/chromadb-ipv6:latest
   ```

4. **Update Railway:**
   - Go to your Chroma-GjDQ service in Railway
   - Change the Docker image from `ghcr.io/chroma-core/chroma:latest` to `yourusername/chromadb-ipv6:latest`
   - Railway will redeploy with IPv6 support

## How It Works

The simple solution (Dockerfile.simple) modifies ChromaDB to listen on `::` (all IPv6 interfaces) instead of `0.0.0.0`. On most systems, this enables dual-stack binding, allowing connections from both IPv4 and IPv6 clients.

## Alternative Solution

If the simple solution doesn't work, we also provide a more complex solution using `socat` as a dual-stack proxy (see Dockerfile and docker-entrypoint.sh).

## Verification

After deployment, your Chroma MCP service should be able to connect using:
```
CHROMA_HOST=chroma-gjdq.railway.internal
CHROMA_PORT=8000
CHROMA_SSL=false
```