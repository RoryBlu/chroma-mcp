# Claude Code Instructions: Add Custom Embedding API Support to Chroma MCP

## Overview
Modify Chroma MCP to support custom embedding API endpoints that don't require authentication. The current implementation only supports predefined providers (OpenAI, Cohere, etc.). We need to add support for arbitrary HTTP embedding endpoints.

## Requirements

### Environment Variables to Support
The implementation should recognize these environment variables:
- `EMBEDDINGS_API_URL` - The full URL endpoint for the custom embeddings service
- `EMBEDDING_MODEL` - The model name to use (passed to the API)
- `EMBEDDING_DIMENSION` - The vector dimension size (for validation)

Example values:
```bash
EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

## Implementation Steps

### 1. Create Custom Embedding Function Class

Create a new embedding function class that:
- Inherits from Chroma's `EmbeddingFunction` protocol
- Reads the custom environment variables
- Makes HTTP POST requests to the custom API endpoint
- Handles batch processing of documents
- Returns embeddings in the format Chroma expects

The class should:
- Check if all required environment variables are set
- Validate that returned embeddings match the expected dimension
- Handle API errors gracefully
- Support batch embedding of multiple documents

### 2. Modify Chroma MCP Server

Find where Chroma MCP initializes embedding functions and:
- Add a new embedding function type called "custom" or "http"
- Check for the custom embedding environment variables
- If they exist, instantiate the custom embedding function
- Make it available as an option when creating collections

### 3. API Request Format

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

### 4. Integration Points

Look for these key areas in the Chroma MCP codebase:
- Where embedding functions are initialized/configured
- The mapping of embedding function names to classes
- Collection creation logic that sets the embedding function
- Environment variable loading logic

### 5. Configuration Priority

The custom embedding function should be used when:
1. The `EMBEDDINGS_API_URL` environment variable is set
2. No other specific embedding provider is configured
3. The user hasn't explicitly chosen a different embedding function

### 6. Error Handling

Implement proper error handling for:
- Missing environment variables (provide clear error messages)
- API connection failures
- Invalid API responses
- Dimension mismatches between configured and actual embeddings
- Rate limiting or timeout issues

### 7. Testing Considerations

Add tests or test manually:
- Creating a collection with custom embeddings
- Adding documents to the collection
- Querying the collection
- Verifying embeddings have correct dimensions
- Handling API failures gracefully

## Code Structure Suggestions

1. **New file**: `custom_embedding_function.py` (or similar)
   - Contains the CustomEmbeddingFunction class
   - Handles all HTTP communication with the API

2. **Modify**: The main server file where embedding functions are registered
   - Add custom embedding function to the available options
   - Check for custom embedding environment variables

3. **Update**: Any configuration or initialization logic
   - Ensure custom embeddings are properly initialized when env vars are present

## Additional Notes

- The Railway API endpoint doesn't require authentication (no API key needed)
- The API follows OpenAI's embedding API format for compatibility
- Ensure backward compatibility - existing Chroma MCP functionality should remain unchanged
- Consider adding logging for debugging custom embedding requests
- The implementation should be clean and follow Chroma's coding patterns

## Expected Outcome

After implementation, users should be able to:
1. Set the three environment variables in their `.env` file or system
2. Start Chroma MCP normally
3. Create collections that automatically use the custom embedding service
4. All embedding operations (add, query) should use the Railway API transparently

The custom embeddings should work seamlessly without users needing to specify anything beyond the environment variables.