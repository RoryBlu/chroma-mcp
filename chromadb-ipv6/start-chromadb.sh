#!/bin/bash
set -e

# Start ChromaDB with :: (all IPv6 interfaces) which should also bind to IPv4
# The :: address is the IPv6 equivalent of 0.0.0.0 and on most systems will bind to both IPv4 and IPv6
exec uvicorn chromadb.app:app \
    --host :: \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --log-config chromadb/log_config.yml \
    --timeout-keep-alive 30