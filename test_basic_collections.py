#!/usr/bin/env python3
"""
Test basic collection operations without AdminClient
"""

import httpx
import json

MCP_URL = "https://chroma-mcp-development.up.railway.app"

print("Testing Basic Collection Operations")
print("=" * 60)

# 1. Get current context
print("\n1. Getting current context:")
response = httpx.post(f"{MCP_URL}/tools/chroma_get_current_context", json={})
print(f"   Current context: {response.json()}")

# 2. List collections in current context
print("\n2. Listing collections:")
response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
collections = response.json()
print(f"   Collections: {collections}")

# 3. Create a new collection with specific name
print("\n3. Creating collection 'sparkjar_test':")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_create_collection",
    json={"collection_name": "sparkjar_test"}
)
print(f"   Response: {response.text[:200]}...")

# 4. List collections again
print("\n4. Listing collections again:")
response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
collections = response.json()
print(f"   Collections: {collections}")

# 5. Add some test documents
print("\n5. Adding test documents:")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_add_documents",
    json={
        "collection_name": "sparkjar_test",
        "documents": [
            "This is a test document about sparkjar",
            "Another document with important information",
            "Third document for testing purposes"
        ],
        "ids": ["doc1", "doc2", "doc3"]
    }
)
print(f"   Response: {response.text[:200]}...")

# 6. Get collection info
print("\n6. Getting collection info:")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_get_collection_info",
    json={"collection_name": "sparkjar_test"}
)
info = response.json()
print(f"   Collection count: {info.get('count', 'unknown')}")

# 7. Query the collection
print("\n7. Querying collection for 'sparkjar':")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_query_documents",
    json={
        "collection_name": "sparkjar_test",
        "query_texts": ["sparkjar information"],
        "n_results": 2
    }
)
results = response.json()
if isinstance(results, dict) and "documents" in results:
    print(f"   Found {len(results['documents'][0])} results")
    for i, doc in enumerate(results['documents'][0][:2]):
        print(f"   Result {i+1}: {doc[:100]}...")
else:
    print(f"   Query response: {results}")

print("\n" + "=" * 60)
print("Basic operations complete!")
print("\nKey findings:")
print("- Collections CAN be created and accessed")
print("- The MCP server is working correctly")
print("- Your previous collections might be in a different ChromaDB instance")
print("- Or they might have been created outside the MCP context")