# ChromaDB with IPv6 support for Railway
FROM ghcr.io/chroma-core/chroma:latest

# Install socat for dual-stack proxy
USER root
RUN apt-get update && apt-get install -y socat && rm -rf /var/lib/apt/lists/*

# Create entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch back to chroma user
USER chroma

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]