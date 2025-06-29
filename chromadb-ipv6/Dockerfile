# ChromaDB with IPv6 support for Railway
FROM ghcr.io/chroma-core/chroma:latest

# ChromaDB ignores CHROMA_HOST_ADDR env var - must use command line
# Override the default command to force IPv6 binding
CMD ["uvicorn", "chromadb.app:app", "--host", "::", "--port", "8000", "--workers", "1", "--proxy-headers", "--log-config", "chromadb/log_config.yml", "--timeout-keep-alive", "30"]