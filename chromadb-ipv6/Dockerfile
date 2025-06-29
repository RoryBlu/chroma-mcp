# ChromaDB with IPv6 support for Railway
FROM ghcr.io/chroma-core/chroma:latest

# CRITICAL: Set ChromaDB to bind to IPv6 for Railway private networking
# Note: This makes it IPv6-only, so public IPv4 access won't work
ENV CHROMA_HOST_ADDR=::

# The original image should handle everything else