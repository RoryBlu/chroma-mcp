# Custom Embedding API Support

Chroma MCP now supports custom embedding APIs that don't require authentication! This is perfect for DIY and open-source embedding servers.

## Quick Setup

1. Set these environment variables in your `.env` file:

```bash
# Custom Embedding API Configuration
EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

2. Start Chroma MCP normally - it will automatically detect and use your custom embedding service!

## How It Works

When the environment variables are set, Chroma MCP will:
- ✅ Automatically register a "custom" embedding function
- ✅ Auto-select it as the default for new collections
- ✅ Handle all embedding operations transparently through your API
- ✅ Maintain full compatibility with existing embedding providers

## API Requirements

Your embedding API should follow the OpenAI-compatible format:

**Endpoint**: `POST {EMBEDDINGS_API_URL}/embeddings`

**Request**:
```json
{
  "model": "your-model-name",
  "input": ["text1", "text2", ...],
  "encoding_format": "float"
}
```

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.1, 0.2, ...],
      "index": 0
    }
  ],
  "model": "your-model-name",
  "usage": {
    "prompt_tokens": 123,
    "total_tokens": 123
  }
}
```

## Usage Examples

### Auto-Selection (Recommended)
```python
# Will automatically use custom embeddings if configured
await mcp.call_tool("chroma_create_collection", {
    "collection_name": "my_collection"
})
```

### Explicit Selection
```python
# Explicitly choose custom embeddings
await mcp.call_tool("chroma_create_collection", {
    "collection_name": "my_collection",
    "embedding_function_name": "custom"
})
```

### Fallback to Built-in Providers
```python
# Still works with existing providers
await mcp.call_tool("chroma_create_collection", {
    "collection_name": "my_collection", 
    "embedding_function_name": "openai"  # or "cohere", "default", etc.
})
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EMBEDDINGS_API_URL` | Yes | Full URL to your embedding service |
| `EMBEDDING_MODEL` | Yes | Model name to pass to your API |
| `EMBEDDING_DIMENSION` | No | Vector dimension (default: 768) |

## Benefits

- 🚀 **No API Keys Required** - Perfect for open-source deployments
- 🔧 **DIY Friendly** - Use any embedding model you want
- 💰 **Cost Control** - Run your own embedding infrastructure
- 🔒 **Privacy** - Keep your data on your own servers
- ⚡ **Performance** - Optimize for your specific use case

## Troubleshooting

If you encounter issues:

1. **Check Environment Variables**: Ensure `EMBEDDINGS_API_URL` and `EMBEDDING_MODEL` are set
2. **Test API Connectivity**: Make sure your embedding API is accessible
3. **Verify Response Format**: Ensure your API returns OpenAI-compatible responses
4. **Check Dimensions**: Verify the embedding dimension matches your configuration

The implementation includes comprehensive error handling and will provide clear error messages to help you debug any issues.