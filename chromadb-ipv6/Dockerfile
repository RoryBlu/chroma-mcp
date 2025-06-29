# ChromaDB with IPv6 support for Railway - Version 2
FROM ghcr.io/chroma-core/chroma:latest

# We need to find out what the original entrypoint/cmd is
# For now, let's try to work with the existing setup
USER root

# Create a wrapper script that calls the original entrypoint
RUN echo '#!/bin/bash' > /start-wrapper.sh && \
    echo 'echo "=== ChromaDB IPv6 Wrapper ===="' >> /start-wrapper.sh && \
    echo 'echo "Railway Private Domain: ${RAILWAY_PRIVATE_DOMAIN}"' >> /start-wrapper.sh && \
    echo 'echo "Port: ${PORT:-8000}"' >> /start-wrapper.sh && \
    echo '# Call the original ChromaDB entrypoint' >> /start-wrapper.sh && \
    echo 'exec /chroma/bin/python -m uvicorn chromadb.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${CHROMA_WORKERS:-1} --proxy-headers --log-config chromadb/log_config.yml --timeout-keep-alive ${CHROMA_TIMEOUT_KEEP_ALIVE:-30}' >> /start-wrapper.sh && \
    chmod +x /start-wrapper.sh

EXPOSE 8000

# Switch back to chroma user
USER chroma

ENTRYPOINT ["/start-wrapper.sh"]