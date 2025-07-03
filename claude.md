# Claude Code Instructions: Custom Embedding API Support in Chroma MCP

## Overview
Custom embedding API support has been implemented in Chroma MCP. This feature allows using arbitrary HTTP embedding endpoints that don't require authentication by configuring environment variables. The implementation is located in `src/chroma_mcp/server.py`.

## Current Implementation

### Environment Variables
The implementation recognizes these environment variables:
- `EMBEDDINGS_API_URL` - The full URL endpoint for the custom embeddings service (automatically appends `/embeddings` if not present)
- `EMBEDDING_MODEL` - The model name to use (passed to the API)
- `EMBEDDING_DIMENSION` - The vector dimension size (used for validation)

Example values:
```bash
EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

### Implementation Details

1. **CustomEmbeddingFunction Class** (lines 32-81 in `src/chroma_mcp/server.py`):
   - Inherits from Chroma's `EmbeddingFunction` protocol
   - Reads environment variables on initialization
   - Makes HTTP POST requests using httpx
   - Validates embedding dimensions match the configured value
   - Handles errors gracefully (connection errors, HTTP errors, invalid responses)

2. **Registration and Configuration** (lines 357-369):
   - `_register_custom_embedding_if_available()` checks for custom embedding environment variables
   - Registers `CustomEmbeddingFunction` as "custom" when variables are set
   - `_get_default_embedding_function()` returns "custom" as default when configured

3. **Integration** (line 141):
   - Called in `get_chroma_client()` to ensure availability during client initialization

### API Request Format

The custom embedding API expects:
- **Endpoint**: `POST {EMBEDDINGS_API_URL}/embeddings`
- **Request body**:
  ```json
  {
    "model": "{EMBEDDING_MODEL}",
    "input": ["text1", "text2", ...],
    "encoding_format": "float"
  }
  ```
- **Response format**:
  ```json
  {
    "object": "list",
    "data": [
      {
        "object": "embedding",
        "embedding": [0.1, 0.2, ...],
        "index": 0
      },
      ...
    ],
    "model": "{EMBEDDING_MODEL}",
    "usage": {
      "prompt_tokens": 123,
      "total_tokens": 123
    }
  }
  ```

### How It Works

1. **Automatic Registration**: When `EMBEDDINGS_API_URL` and `EMBEDDING_MODEL` are set, the custom embedding function is automatically registered.

2. **Default Selection**: If no embedding function is specified when creating a collection, "custom" becomes the default when custom embeddings are configured.

3. **Explicit Usage**: Users can explicitly specify `"embedding_function_name": "custom"` when creating collections.

### Error Handling

The implementation handles:
- Missing environment variables (raises ValueError with clear messages)
- API connection failures (raises Exception with connection error details)
- HTTP errors (raises Exception with status code and response)
- Invalid API responses (raises Exception if response format is incorrect)
- Dimension mismatches (raises ValueError if actual dimensions don't match configured)

## Additional Notes

- The Railway API endpoint doesn't require authentication (no API key needed)
- The API follows OpenAI's embedding API format for compatibility
- Ensure backward compatibility - existing Chroma MCP functionality should remain unchanged
- Consider adding logging for debugging custom embedding requests
- The implementation should be clean and follow Chroma's coding patterns

## Usage

To use custom embeddings:
1. Set the three environment variables in your `.env` file or system
2. Start Chroma MCP normally
3. Create collections - they will automatically use the custom embedding service
4. All embedding operations (add, query) will use your custom API transparently

The custom embeddings work seamlessly without needing to specify anything beyond the environment variables.

## Development Principles

When working on this codebase, always follow these principles:
- **KISS (Keep It Simple, Stupid)**: Prefer simple, readable solutions over clever or complex ones
- **Discipline**: Write clean, consistent code that follows established patterns
- **Verify Everything**: Test assumptions, validate inputs, and verify outputs before considering any task complete
- **No Overcomplicated Code**: If a solution seems complex, step back and find a simpler approach

## Future Improvements

Potential enhancements to consider:
- Add retry logic for transient HTTP failures
- Support custom headers for authenticated endpoints
- Add comprehensive unit tests for the CustomEmbeddingFunction
- Update README.md to document this feature
- Add support for configurable timeout values
- Implement request/response logging for debugging