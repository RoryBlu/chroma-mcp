#!/usr/bin/env python3
"""
Simple test to try different tenant combinations
"""

import httpx
import json

MCP_URL = "https://chroma-mcp-development.up.railway.app"

print("Testing Different Tenant/Database Combinations")
print("=" * 60)

# Test combinations
test_cases = [
    ("default_tenant", "default_database"),
    ("default", "default"),
    ("main", "main"),
    ("sparkjar", "sparkjar"),
    ("sparkjar-crew", "sparkjar-crew"),
    ("", ""),  # Empty strings
]

for tenant, database in test_cases:
    print(f"\nTesting tenant='{tenant}', database='{database}':")
    
    # Switch context
    response = httpx.post(
        f"{MCP_URL}/tools/chroma_switch_context",
        json={"tenant": tenant, "database": database}
    )
    print(f"  Switch context response: {response.status_code}")
    
    if response.status_code == 200:
        # List collections
        response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
        collections = response.json()
        
        if isinstance(collections, list):
            if collections and collections[0] != "__NO_COLLECTIONS_FOUND__":
                print(f"  ✓ FOUND COLLECTIONS: {collections}")
            else:
                print(f"  ✗ No collections found")
        else:
            print(f"  Error: {collections}")

print("\n" + "=" * 60)
print("Testing complete!")