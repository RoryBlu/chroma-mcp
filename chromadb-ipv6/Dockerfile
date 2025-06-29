# ChromaDB with IPv6 support for Railway
FROM ghcr.io/chroma-core/chroma:latest

# Stay as root for debugging
USER root

# Install debugging tools
RUN apt-get update && apt-get install -y net-tools iputils-ping && rm -rf /var/lib/apt/lists/*

# Copy our start script
COPY start-chromadb.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start-chromadb.sh

EXPOSE 8000

# Run as root for now to debug
CMD ["/usr/local/bin/start-chromadb.sh"]