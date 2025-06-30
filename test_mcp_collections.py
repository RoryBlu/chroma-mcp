#!/usr/bin/env python3
"""
Test MCP server collection operations
"""

import httpx
import json

MCP_URL = "https://chroma-mcp-development.up.railway.app"

print("Testing MCP Server Collection Operations")
print("=" * 50)

# Test 1: List collections
print("\n1. List collections:")
response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
print(f"   Response: {response.json()}")

# Test 2: Create a test collection
print("\n2. Create test collection:")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_create_collection", 
    json={"collection_name": "mcp_test_collection"}
)
print(f"   Response: {response.text}")

# Test 3: List collections again
print("\n3. List collections again:")
response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
print(f"   Response: {response.json()}")

# Test 4: Get collection info
print("\n4. Get collection info:")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_get_collection_info",
    json={"collection_name": "mcp_test_collection"}
)
print(f"   Response: {response.text}")

# Test 5: Add a document
print("\n5. Add document to collection:")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_add_documents",
    json={
        "collection_name": "mcp_test_collection",
        "documents": ["This is a test document from MCP collection test"],
        "ids": ["test_doc_1"]
    }
)
print(f"   Response: {response.text}")

# Test 6: Get collection count
print("\n6. Get collection count:")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_get_collection_count",
    json={"collection_name": "mcp_test_collection"}
)
print(f"   Response: {response.text}")

print("\n" + "=" * 50)
print("Testing complete!")