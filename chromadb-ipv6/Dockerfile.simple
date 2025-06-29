# ChromaDB with IPv6 support for Railway - Simple version
FROM ghcr.io/chroma-core/chroma:latest

# Create a simple wrapper script
USER root
COPY start-chromadb.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start-chromadb.sh
USER chroma

EXPOSE 8000

CMD ["/usr/local/bin/start-chromadb.sh"]