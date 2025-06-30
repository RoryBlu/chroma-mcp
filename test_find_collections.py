#!/usr/bin/env python3
"""
Test the new admin functionality to find all collections
"""

import httpx
import json

MCP_URL = "https://chroma-mcp-development.up.railway.app"

print("Testing MCP Admin Functionality")
print("=" * 60)

# Test 1: Get current context
print("\n1. Get current context:")
response = httpx.post(f"{MCP_URL}/tools/chroma_get_current_context", json={})
print(f"   Current context: {response.json()}")

# Test 2: List databases
print("\n2. List databases in default tenant:")
response = httpx.post(f"{MCP_URL}/tools/chroma_list_databases", json={})
databases = response.json()
if isinstance(databases, list):
    print(f"   Found {len(databases)} databases:")
    for db in databases:
        if isinstance(db, dict):
            print(f"   - {db['name']} (tenant: {db['tenant']})")
        else:
            print(f"   - {db}")
else:
    print(f"   Response: {databases}")

# Test 3: List all collections across all databases
print("\n3. List all collections across all databases:")
response = httpx.post(f"{MCP_URL}/tools/chroma_list_all_collections", json={})
all_collections = response.json()
print(f"   Collections by database:")
for db_name, collections in all_collections.items():
    print(f"   Database '{db_name}':")
    if collections:
        for col in collections:
            print(f"     - {col}")
    else:
        print("     (no collections)")

# Test 4: If we found databases with collections, switch context
if all_collections:
    # Find a database with collections
    for db_name, collections in all_collections.items():
        if collections and db_name != "default_database":
            print(f"\n4. Switching to database '{db_name}' which has collections:")
            response = httpx.post(
                f"{MCP_URL}/tools/chroma_switch_context",
                json={"database": db_name}
            )
            print(f"   New context: {response.json()}")
            
            # List collections in this database
            print(f"\n5. List collections after switching:")
            response = httpx.post(f"{MCP_URL}/tools/chroma_list_collections", json={})
            print(f"   Collections: {response.json()}")
            
            # Get info about the first collection
            if collections:
                print(f"\n6. Get info about collection '{collections[0]}':")
                response = httpx.post(
                    f"{MCP_URL}/tools/chroma_get_collection_info",
                    json={"collection_name": collections[0]}
                )
                print(f"   Collection info: {json.dumps(response.json(), indent=2)}")
            break

print("\n" + "=" * 60)
print("Testing complete!")
print("\nSummary:")
if isinstance(databases, list):
    print(f"- Found {len(databases)} databases")
if isinstance(all_collections, dict):
    total_collections = sum(len(cols) for cols in all_collections.values())
    print(f"- Found {total_collections} total collections across all databases")
    if total_collections > 1:  # Exclude just the test collection
        print("\nYour collections are likely in one of the databases listed above!")
    else:
        print("\nNo collections found beyond the test collection.")
        print("Your sparkjar-crew collections might be in a different tenant.")