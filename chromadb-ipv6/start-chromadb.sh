#!/bin/bash
set -e

echo "=== ChromaDB IPv6 Debug Info ==="
echo "Hostname: $(hostname)"
echo "Network interfaces:"
ip addr show
echo "================================"

# For Railway, we need to listen on the PORT environment variable if set
PORT=${PORT:-8000}
echo "Using port: $PORT"

# Start ChromaDB
# Using 0.0.0.0 should bind to all available interfaces
echo "Starting ChromaDB server on 0.0.0.0:$PORT..."

# Check if we're in the right directory
cd /chroma || cd /app || cd /

# Start ChromaDB using the same command as the original container
exec python -m chromadb.cli.cli run --host 0.0.0.0 --port $PORT --path /chroma/chroma --log-config chromadb/log_config.yml