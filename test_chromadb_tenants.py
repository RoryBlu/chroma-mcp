#!/usr/bin/env python3
"""
Test different tenant/database combinations to find collections
"""

import chromadb
import os
from chromadb.config import Settings

# Configuration
# Check if we have a public URL first
CHROMA_PUBLIC_URL = os.environ.get('CHROMA_PUBLIC_URL')
if CHROMA_PUBLIC_URL:
    # Parse the public URL
    from urllib.parse import urlparse
    parsed = urlparse(CHROMA_PUBLIC_URL)
    CHROMA_HOST = parsed.hostname
    CHROMA_PORT = parsed.port or (443 if parsed.scheme == 'https' else 80)
    CHROMA_SSL = parsed.scheme == 'https'
else:
    # Fall back to individual settings
    CHROMA_HOST = os.environ.get('CHROMA_HOST', 'chroma-gjdq.railway.internal')
    CHROMA_PORT = int(os.environ.get('CHROMA_PORT', '8080'))
    CHROMA_SSL = os.environ.get('CHROMA_SSL', 'false').lower() == 'true'

CHROMA_CUSTOM_AUTH_CREDENTIALS = os.environ.get('CHROMA_CUSTOM_AUTH_CREDENTIALS', 'gi9v25dw33k086falw1c1i5m55b2uynt')

# Test different tenant/database combinations
test_combinations = [
    # Default combination
    ("default_tenant", "default_database"),
    # Common alternatives
    ("default", "default"),
    ("main", "main"),
    ("sparkjar", "sparkjar"),
    ("sparkjar-crew", "sparkjar-crew"),
    # No tenant/database (let ChromaDB use its defaults)
    (None, None),
]

print(f"Testing ChromaDB connections to {CHROMA_HOST}:{CHROMA_PORT}")
print(f"SSL: {CHROMA_SSL}, Auth: {'Yes' if CHROMA_CUSTOM_AUTH_CREDENTIALS else 'No'}")
print("=" * 60)

for tenant, database in test_combinations:
    print(f"\nTesting tenant='{tenant}', database='{database}'")
    print("-" * 40)
    
    try:
        # Prepare settings
        settings = Settings()
        if CHROMA_CUSTOM_AUTH_CREDENTIALS:
            settings = Settings(
                chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                chroma_client_auth_credentials=CHROMA_CUSTOM_AUTH_CREDENTIALS
            )
        
        # Create client with specific tenant/database
        client_kwargs = {
            "host": CHROMA_HOST,
            "port": CHROMA_PORT,
            "ssl": CHROMA_SSL,
            "settings": settings
        }
        
        if tenant is not None:
            client_kwargs["tenant"] = tenant
        if database is not None:
            client_kwargs["database"] = database
            
        client = chromadb.HttpClient(**client_kwargs)
        
        # Try to list collections
        collections = client.list_collections()
        
        if collections:
            print(f"  SUCCESS! Found {len(collections)} collections:")
            for col in collections:
                print(f"    - {col.name}")
                # Try to get collection count
                try:
                    count = col.count()
                    print(f"      Documents: {count}")
                except:
                    pass
        else:
            print("  No collections found (empty database)")
            
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        if "404" in str(e):
            print("    (Tenant/database combination doesn't exist)")

print("\n" + "=" * 60)
print("Testing complete!")

# Additional test: try to get server info
print("\nTrying to get server info...")
try:
    # Use default tenant/database
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        ssl=CHROMA_SSL,
        settings=settings if 'settings' in locals() else Settings()
    )
    
    # Try heartbeat
    response = client.heartbeat()
    print(f"Heartbeat response: {response}")
    
except Exception as e:
    print(f"Heartbeat error: {e}")