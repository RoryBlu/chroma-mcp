#!/usr/bin/env python3
"""
Find collections by trying common database names in default tenant
"""

import httpx
import json

MCP_URL = "https://chroma-mcp-development.up.railway.app"

print("Searching for Collections in Different Databases")
print("=" * 60)

# First, get back to default tenant/database
response = httpx.post(
    f"{MCP_URL}/tools/chroma_switch_context",
    json={"tenant": "default_tenant", "database": "default_database"}
)
print(f"Reset to default context: {response.json()}")

# Test different database names within default_tenant
database_names = [
    "default_database",
    "default",
    "main",
    "primary",
    "sparkjar",
    "sparkjar-crew",
    "sparkjar_crew",
    "collections",
    "data",
    "production",
    "dev",
    "development",
    "test",
    "chroma",
    "chromadb",
]

found_collections = {}

for db_name in database_names:
    print(f"\nTrying database '{db_name}':")
    
    # Switch to this database
    response = httpx.post(
        f"{MCP_URL}/tools/chroma_switch_context",
        json={"database": db_name}
    )
    
    if response.status_code == 200:
        # List collections
        response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
        collections = response.json()
        
        if isinstance(collections, list):
            if collections and collections[0] != "__NO_COLLECTIONS_FOUND__":
                print(f"  ✓ FOUND {len(collections)} COLLECTIONS!")
                found_collections[db_name] = collections
                for col in collections:
                    print(f"    - {col}")
            else:
                print(f"  ✗ No collections (empty database)")
        elif isinstance(collections, dict) and "detail" in collections:
            if "not found" in collections["detail"]:
                print(f"  ✗ Database doesn't exist")
            else:
                print(f"  Error: {collections['detail']}")
        else:
            print(f"  Response: {collections}")

print("\n" + "=" * 60)
print("Summary:")
if found_collections:
    print(f"\nFound collections in {len(found_collections)} database(s):")
    for db_name, collections in found_collections.items():
        print(f"\nDatabase '{db_name}':")
        for col in collections:
            print(f"  - {col}")
else:
    print("\nNo collections found in any of the tested databases.")
    print("\nPossible reasons:")
    print("1. Collections might be stored with persistence that wasn't properly mounted")
    print("2. Collections might have been created with a different ChromaDB instance")
    print("3. The sparkjar-crew tool might have used a different storage backend")
    print("\nYou may need to recreate your collections from the original data sources.")