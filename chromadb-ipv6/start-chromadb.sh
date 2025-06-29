#!/bin/bash
set -e

echo "=== ChromaDB IPv6 Startup ==="
echo "Hostname: $(hostname)"
echo "Railway Private Domain: ${RAILWAY_PRIVATE_DOMAIN}"

# Try to show network info if available
if command -v ip &> /dev/null; then
    echo "Network interfaces:"
    ip addr show | grep -E 'inet6?|^[0-9]+:' || true
elif command -v ifconfig &> /dev/null; then
    echo "Network interfaces:"
    ifconfig | grep -E 'inet6?|^[A-Za-z]' || true
fi

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
echo "  Python: $(which python)"
echo "  PWD: $(pwd)"

# Find Python executable
PYTHON_CMD=""
for cmd in python3 python python3.11 python3.10 python3.9; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        echo "  Python: $(which $cmd)"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: No Python interpreter found!"
    echo "PATH=$PATH"
    ls -la /usr/bin/python* 2>/dev/null || true
    ls -la /usr/local/bin/python* 2>/dev/null || true
    exit 1
fi

# Ensure we're in the right directory
cd /chroma 2>/dev/null || true

echo "Starting ChromaDB server..."
echo "Command: $PYTHON_CMD -m uvicorn chromadb.app:app --host $HOST --port $PORT"

# Start ChromaDB using Python module to ensure we use the right environment
exec $PYTHON_CMD -m uvicorn chromadb.app:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --proxy-headers \
    --log-config chromadb/log_config.yml \
    --timeout-keep-alive "${CHROMA_TIMEOUT_KEEP_ALIVE:-30}"