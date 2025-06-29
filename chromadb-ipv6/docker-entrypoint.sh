#!/bin/bash
set -e

echo "Starting ChromaDB with IPv6 support..."

# Start socat to forward IPv6 connections to ChromaDB's IPv4 interface
# This creates a dual-stack proxy that listens on both IPv4 and IPv6
socat TCP6-LISTEN:8000,reuseaddr,fork TCP4:127.0.0.1:8001 &
SOCAT_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    kill $SOCAT_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup EXIT SIGTERM SIGINT

# Start ChromaDB on localhost:8001 (IPv4 only)
# Pass all arguments to the original ChromaDB command
exec uvicorn chromadb.app:app --host 127.0.0.1 --port 8001 --workers 1 --proxy-headers --log-config chromadb/log_config.yml --timeout-keep-alive 30 "$@"