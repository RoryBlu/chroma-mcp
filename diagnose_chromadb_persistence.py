#!/usr/bin/env python3
"""
Diagnose ChromaDB persistence issues on Railway
"""

import httpx
import json
import sys
import os

# Configuration from environment or defaults
CHROMA_HOST = os.environ.get('CHROMA_HOST', 'chroma-gjdq.railway.internal')
CHROMA_PORT = os.environ.get('CHROMA_PORT', '8080')
CHROMA_SSL = os.environ.get('CHROMA_SSL', 'false').lower() == 'true'
CHROMA_CUSTOM_AUTH_CREDENTIALS = os.environ.get('CHROMA_CUSTOM_AUTH_CREDENTIALS', 'gi9v25dw33k086falw1c1i5m55b2uynt')

# Use public URL if provided for testing
PUBLIC_URL = os.environ.get('CHROMA_PUBLIC_URL', '')

def main():
    # Determine base URL
    if PUBLIC_URL:
        base_url = PUBLIC_URL.rstrip('/')
        print(f"Using public URL: {base_url}")
    else:
        protocol = 'https' if CHROMA_SSL else 'http'
        base_url = f"{protocol}://{CHROMA_HOST}:{CHROMA_PORT}"
        print(f"Using private URL: {base_url}")
    
    # Create client with auth
    headers = {}
    if CHROMA_CUSTOM_AUTH_CREDENTIALS:
        headers['Authorization'] = f'Bearer {CHROMA_CUSTOM_AUTH_CREDENTIALS}'
    
    client = httpx.Client(headers=headers, timeout=30.0)
    
    try:
        # 1. Check ChromaDB health
        print("\n1. Checking ChromaDB health...")
        try:
            response = client.get(f"{base_url}/api/v1/heartbeat")
            print(f"   Heartbeat: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 2. Get version info
        print("\n2. Getting ChromaDB version...")
        try:
            response = client.get(f"{base_url}/api/v1/version")
            if response.status_code == 200:
                print(f"   Version: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 3. List collections
        print("\n3. Listing collections...")
        try:
            response = client.get(f"{base_url}/api/v1/collections")
            if response.status_code == 200:
                collections = response.json()
                print(f"   Found {len(collections)} collections:")
                for col in collections:
                    print(f"   - {col.get('name', 'Unknown')} (id: {col.get('id', 'Unknown')})")
                    if 'metadata' in col:
                        print(f"     Metadata: {col['metadata']}")
            else:
                print(f"   Error: Status {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 4. Check persistence configuration
        print("\n4. Checking persistence configuration...")
        print(f"   PERSIST_DIRECTORY env var: {os.environ.get('PERSIST_DIRECTORY', 'Not set')}")
        print(f"   IS_PERSISTENT env var: {os.environ.get('IS_PERSISTENT', 'Not set')}")
        
        # 5. Try to create a test collection
        print("\n5. Creating test collection...")
        try:
            test_collection_name = "persistence_diagnostic_test"
            response = client.post(
                f"{base_url}/api/v1/collections",
                json={
                    "name": test_collection_name,
                    "metadata": {"created_by": "diagnostic_script"}
                }
            )
            if response.status_code in [200, 201]:
                print(f"   Successfully created collection: {test_collection_name}")
                
                # Add a test document
                col_response = client.get(f"{base_url}/api/v1/collections/{test_collection_name}")
                if col_response.status_code == 200:
                    col_data = col_response.json()
                    col_id = col_data['id']
                    
                    print(f"\n6. Adding test document to collection...")
                    add_response = client.post(
                        f"{base_url}/api/v1/collections/{col_id}/add",
                        json={
                            "documents": ["This is a test document for persistence verification"],
                            "ids": ["test_doc_1"],
                            "metadatas": [{"purpose": "persistence_test"}]
                        }
                    )
                    if add_response.status_code == 200:
                        print("   Successfully added test document")
                    else:
                        print(f"   Failed to add document: {add_response.status_code}")
                        print(f"   Response: {add_response.text}")
            else:
                print(f"   Failed to create collection: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 7. Summary
        print("\n" + "="*50)
        print("DIAGNOSIS SUMMARY:")
        print("="*50)
        print("\nTo verify persistence:")
        print("1. Note the collections listed above")
        print("2. Restart/redeploy your ChromaDB service in Railway")
        print("3. Run this script again")
        print("4. If collections are missing after restart, you have a persistence issue")
        print("\nTo fix persistence issues:")
        print("1. Add a persistent volume in Railway (Settings → Volumes)")
        print("2. Mount it to /chroma-data")
        print("3. Set PERSIST_DIRECTORY=/chroma-data in environment variables")
        print("4. Set IS_PERSISTENT=TRUE in environment variables")
        print("5. Redeploy with the updated configuration")
        
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()