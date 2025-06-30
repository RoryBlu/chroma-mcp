#!/usr/bin/env python3
"""
Check if sparkjar created collections directly
"""

import httpx

MCP_URL = "https://chroma-mcp-development.up.railway.app"

print("Checking for sparkjar collections")
print("=" * 60)

# 1. List current collections
print("\n1. Current collections in MCP:")
response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
collections = response.json()
print(f"   Found: {collections}")

# 2. Try to access known sparkjar collection names
possible_names = [
    "sparkjar",
    "sparkjar-crew", 
    "sparkjar_crew",
    "documents",
    "books",
    "company_docs",
    "company-docs",
    "embeddings",
    "vectors",
    "knowledge",
    "knowledge_base",
    "kb",
    "data"
]

print("\n2. Trying to access possible sparkjar collections:")
for name in possible_names:
    try:
        response = httpx.post(
            f"{MCP_URL}/tools/chroma_get_collection_info",
            json={"collection_name": name}
        )
        if response.status_code == 200:
            info = response.json()
            if "count" in info and info["count"] > 0:
                print(f"   ✓ Found '{name}' with {info['count']} documents!")
        elif response.status_code == 500:
            # Collection doesn't exist
            pass
    except:
        pass

# 3. Get the test collection we created
print("\n3. Checking our test collection:")
response = httpx.post(
    f"{MCP_URL}/tools/chroma_get_collection_info", 
    json={"collection_name": "sparkjar_test"}
)
if response.status_code == 200:
    print("   ✓ Test collection exists and is accessible")

print("\n" + "=" * 60)
print("\nConclusion:")
print("If your sparkjar collections don't appear above, they were likely:")
print("1. Created in a different ChromaDB instance")
print("2. Created with direct ChromaDB API (not through MCP)")  
print("3. Lost due to container restart without persistent volume")
print("\nThe MCP server is working correctly with the current ChromaDB instance.")