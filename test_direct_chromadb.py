#!/usr/bin/env python3
"""
Test ChromaDB directly to find collections
"""

import chromadb
from chromadb.config import Settings

# Configuration from environment
CHROMA_HOST = "chroma-gjdq.up.railway.app"
CHROMA_PORT = 443
CHROMA_SSL = True
CHROMA_AUTH = "gi9v25dw33k086falw1c1i5m55b2uynt"

print("Testing ChromaDB Directly")
print("=" * 60)

# Test 1: Connect with default tenant/database
print("\n1. Connecting with defaults:")
try:
    settings = Settings(
        chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
        chroma_client_auth_credentials=CHROMA_AUTH
    )
    
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        ssl=CHROMA_SSL,
        settings=settings
    )
    
    collections = client.list_collections()
    print(f"   Found {len(collections)} collections:")
    for col in collections:
        print(f"   - {col.name} (count: {col.count()})")
        
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Try different tenant/database combinations
print("\n2. Testing different contexts:")
test_contexts = [
    ("default_tenant", "default_database"),
    ("default_tenant", "default"),
    ("default_tenant", "main"),
    ("default_tenant", "sparkjar"),
    ("sparkjar", "default_database"),
    ("sparkjar", "sparkjar"),
]

for tenant, database in test_contexts:
    print(f"\n   Trying tenant='{tenant}', database='{database}':")
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            ssl=CHROMA_SSL,
            settings=settings,
            tenant=tenant,
            database=database
        )
        
        collections = client.list_collections()
        if collections:
            print(f"   ✓ Found {len(collections)} collections!")
            for col in collections:
                print(f"     - {col.name}")
        else:
            print(f"   ✗ No collections")
            
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            print(f"   ✗ Not found")
        else:
            print(f"   ✗ Error: {error_msg[:100]}...")

# Test 3: Check persistence
print("\n3. Checking persistence configuration:")
try:
    # Get heartbeat to see if server is responsive
    heartbeat = client.heartbeat()
    print(f"   Heartbeat: {heartbeat}")
except Exception as e:
    print(f"   Heartbeat error: {e}")

print("\n" + "=" * 60)
print("Direct ChromaDB test complete!")