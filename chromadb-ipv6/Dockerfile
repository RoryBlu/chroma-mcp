# ChromaDB with IPv6 support for Railway
FROM ghcr.io/chroma-core/chroma:latest

# The ChromaDB image has ENTRYPOINT ["chroma"]
# We need to use the "run" subcommand with proper arguments
CMD ["run", "--host", "::", "--port", "8000"]