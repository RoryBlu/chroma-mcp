#!/bin/bash
set -e

echo "=== ChromaDB IPv6 Debug Info ==="
echo "Hostname: $(hostname)"
echo "Railway Private Domain: ${RAILWAY_PRIVATE_DOMAIN}"
echo "Network interfaces:"
ip addr show | grep -E 'inet6?|^[0-9]+:'
echo "================================"

# Use Railway's PORT or default to 8000
PORT=${PORT:-8000}
HOST=${CHROMA_HOST_ADDR:-0.0.0.0}
WORKERS=${CHROMA_WORKERS:-1}
PERSIST_DIR=${PERSIST_DIRECTORY:-/chroma/chroma}

echo "Configuration:"
echo "  Port: $PORT"
echo "  Host: $HOST"
echo "  Workers: $WORKERS"
echo "  Persist: $PERSIST_DIR"
echo "  Auth Provider: ${CHROMA_SERVER_AUTHN_PROVIDER}"

# Ensure we're in the right directory
cd /chroma 2>/dev/null || cd /app 2>/dev/null || cd /

# Start ChromaDB using the same command structure as the official image
# The official ChromaDB container uses uvicorn directly
exec uvicorn chromadb.app:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --proxy-headers \
    --log-config chromadb/log_config.yml \
    --timeout-keep-alive "${CHROMA_TIMEOUT_KEEP_ALIVE:-30}"