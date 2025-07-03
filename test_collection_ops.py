#!/usr/bin/env python3
"""Test script to verify collection operations are working correctly."""

import asyncio
import os
from src.chroma_mcp.server import (
    chroma_list_collections,
    chroma_get_collection_count,
    chroma_peek_collection,
    chroma_get_documents,
    get_chroma_client
)

async def test_collection_operations():
    """Test the collection operations that were failing."""
    print("Testing collection operations...")
    
    # Initialize the client
    from argparse import Namespace
    args = Namespace(
        client_type='ephemeral',
        data_dir=None,
        host=None,
        port=None,
        custom_auth_credentials=None,
        tenant=None,
        database=None,
        ssl=False,
        api_key=None
    )
    
    # Initialize client
    try:
        client = get_chroma_client(args)
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return
    
    # List collections
    try:
        collections = await chroma_list_collections()
        print(f"✓ List collections: {collections}")
    except Exception as e:
        print(f"✗ Failed to list collections: {e}")
    
    # Test with a collection name
    collection_name = "test_collection"
    
    # Get collection count
    try:
        count_result = await chroma_get_collection_count(collection_name)
        print(f"✓ Get collection count: {count_result}")
        print(f"  Type: {type(count_result)}")
        print(f"  Is dict: {isinstance(count_result, dict)}")
    except Exception as e:
        print(f"✗ Failed to get collection count: {e}")
    
    # Peek collection
    try:
        peek_result = await chroma_peek_collection(collection_name, limit=5)
        print(f"✓ Peek collection: {peek_result}")
        print(f"  Type: {type(peek_result)}")
        print(f"  Keys: {peek_result.keys() if isinstance(peek_result, dict) else 'Not a dict'}")
    except Exception as e:
        print(f"✗ Failed to peek collection: {e}")
    
    # Get documents
    try:
        docs_result = await chroma_get_documents(collection_name, limit=10)
        print(f"✓ Get documents: {docs_result}")
        print(f"  Type: {type(docs_result)}")
        print(f"  Keys: {docs_result.keys() if isinstance(docs_result, dict) else 'Not a dict'}")
    except Exception as e:
        print(f"✗ Failed to get documents: {e}")

if __name__ == "__main__":
    asyncio.run(test_collection_operations())