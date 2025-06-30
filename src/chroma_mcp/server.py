from typing import Dict, List, TypedDict, Union, Optional
from enum import Enum
import chromadb
from chromadb import AdminClient
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
import argparse
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
import ssl
import uuid
import time
import json
from typing_extensions import TypedDict
import httpx
from typing import List as TypingList


from chromadb.api.collection_configuration import (
    CreateCollectionConfiguration
    )
from chromadb.api import EmbeddingFunction
from chromadb.utils.embedding_functions import (
    DefaultEmbeddingFunction,
    CohereEmbeddingFunction,
    OpenAIEmbeddingFunction,
    JinaEmbeddingFunction,
    VoyageAIEmbeddingFunction,
    RoboflowEmbeddingFunction,
)

class CustomEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function that uses an HTTP API endpoint."""
    
    def __init__(self):
        self.api_url = os.getenv('EMBEDDINGS_API_URL')
        self.model = os.getenv('EMBEDDING_MODEL')
        self.dimension = int(os.getenv('EMBEDDING_DIMENSION', '768'))
        
        if not self.api_url:
            raise ValueError("EMBEDDINGS_API_URL environment variable is required for custom embeddings")
        if not self.model:
            raise ValueError("EMBEDDING_MODEL environment variable is required for custom embeddings")
            
        # Ensure API URL ends with /embeddings
        if not self.api_url.endswith('/embeddings'):
            self.api_url = f"{self.api_url.rstrip('/')}/embeddings"
    
    def __call__(self, input: TypingList[str]) -> TypingList[TypingList[float]]:
        """Generate embeddings for a list of input texts."""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.api_url,
                    json={
                        "model": self.model,
                        "input": input,
                        "encoding_format": "float"
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]
                
                # Validate dimensions
                for embedding in embeddings:
                    if len(embedding) != self.dimension:
                        raise ValueError(f"Expected embedding dimension {self.dimension}, got {len(embedding)}")
                        
                return embeddings
                
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to connect to embedding API: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Embedding API returned error {e.response.status_code}: {e.response.text}")
        except KeyError as e:
            raise RuntimeError(f"Invalid response format from embedding API: missing {e}")
        except Exception as e:
            raise RuntimeError(f"Error generating embeddings: {e}")

# Initialize FastMCP server
mcp = FastMCP("chroma")

# Global variables
_chroma_client = None
_admin_client = None
_current_tenant = None
_current_database = None

def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(description='FastMCP server for Chroma DB')
    parser.add_argument('--client-type', 
                       choices=['http', 'cloud', 'persistent', 'ephemeral'],
                       default=os.getenv('CHROMA_CLIENT_TYPE', 'ephemeral'),
                       help='Type of Chroma client to use')
    parser.add_argument('--data-dir',
                       default=os.getenv('CHROMA_DATA_DIR'),
                       help='Directory for persistent client data (only used with persistent client)')
    parser.add_argument('--host', 
                       help='Chroma host (required for http client)', 
                       default=os.getenv('CHROMA_HOST'))
    parser.add_argument('--port', 
                       help='Chroma port (optional for http client)', 
                       default=os.getenv('CHROMA_PORT'))
    parser.add_argument('--custom-auth-credentials',
                       help='Custom auth credentials (optional for http client)', 
                       default=os.getenv('CHROMA_CUSTOM_AUTH_CREDENTIALS'))
    parser.add_argument('--tenant', 
                       help='Chroma tenant (optional for http client)', 
                       default=os.getenv('CHROMA_TENANT'))
    parser.add_argument('--database', 
                       help='Chroma database (required if tenant is provided)', 
                       default=os.getenv('CHROMA_DATABASE'))
    parser.add_argument('--api-key', 
                       help='Chroma API key (required if tenant is provided)', 
                       default=os.getenv('CHROMA_API_KEY'))
    parser.add_argument('--ssl', 
                       help='Use SSL (optional for http client)', 
                       type=lambda x: x.lower() in ['true', 'yes', '1', 't', 'y'],
                       default=os.getenv('CHROMA_SSL', 'true').lower() in ['true', 'yes', '1', 't', 'y'])
    parser.add_argument('--dotenv-path', 
                       help='Path to .env file', 
                       default=os.getenv('CHROMA_DOTENV_PATH', '.chroma_env'))
    return parser

def get_chroma_client(args=None):
    """Get or create the global Chroma client instance."""
    global _chroma_client, _current_tenant, _current_database
    if _chroma_client is None:
        if args is None:
            # Create parser and parse args if not provided
            parser = create_parser()
            args = parser.parse_args()
        
        # Load environment variables from .env file if it exists
        load_dotenv(dotenv_path=args.dotenv_path)
        
        # Check for custom embedding API configuration and register if available
        _register_custom_embedding_if_available()
        if args.client_type == 'http':
            if not args.host:
                raise ValueError("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
            
            settings = Settings()
            if args.custom_auth_credentials:
                settings = Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=args.custom_auth_credentials
                )
            
            # Handle SSL configuration
            try:
                # Prepare kwargs for HttpClient
                client_kwargs = {
                    "host": args.host,
                    "ssl": args.ssl,
                    "settings": settings
                }
                
                # Handle port configuration
                if args.port:
                    client_kwargs["port"] = int(args.port)
                else:
                    # Default to 8000 if no port specified
                    # ChromaDB HttpClient requires a port
                    client_kwargs["port"] = 8000
                
                # Add tenant and database from current context or args
                # These are optional for HTTP client but critical for accessing the right data
                # Use current context first, then args, then defaults
                tenant_to_use = _current_tenant or (args.tenant if args.tenant else DEFAULT_TENANT)
                database_to_use = _current_database or (args.database if args.database else DEFAULT_DATABASE)
                
                client_kwargs["tenant"] = tenant_to_use
                client_kwargs["database"] = database_to_use
                
                # Update current context if not set
                if _current_tenant is None:
                    _current_tenant = tenant_to_use
                if _current_database is None:
                    _current_database = database_to_use
                
                # Debug logging
                print(f"Connecting to ChromaDB:")
                print(f"  Host: {client_kwargs['host']}")
                print(f"  Port: {client_kwargs['port']}")
                print(f"  SSL: {client_kwargs['ssl']}")
                print(f"  Auth: {'Yes' if args.custom_auth_credentials else 'No'}")
                print(f"  Tenant: {client_kwargs.get('tenant', 'default_tenant')}")
                print(f"  Database: {client_kwargs.get('database', 'default_database')}")
                
                # Handle IPv6 connectivity for Railway and other environments
                import socket
                import os
                
                # Detect if we're in an IPv6-only environment (like Railway private network)
                # or if we need to handle dual-stack scenarios
                if args.host:
                    try:
                        # Resolve the hostname to see what addresses are available
                        addrs = socket.getaddrinfo(args.host, client_kwargs['port'], socket.AF_UNSPEC, socket.SOCK_STREAM)
                        ipv4_addrs = [addr for addr in addrs if addr[0] == socket.AF_INET]
                        ipv6_addrs = [addr for addr in addrs if addr[0] == socket.AF_INET6]
                        
                        print(f"  DNS Resolution:")
                        if ipv4_addrs:
                            print(f"    IPv4: {[addr[4][0] for addr in ipv4_addrs]}")
                        if ipv6_addrs:
                            print(f"    IPv6: {[addr[4][0] for addr in ipv6_addrs]}")
                        
                        # If we only have IPv6 addresses (Railway internal), we need to ensure
                        # httpx can connect properly. Check if we're in Railway environment
                        if ipv6_addrs and not ipv4_addrs:
                            print("  Note: Only IPv6 addresses available (Railway private network)")
                            # httpx should handle IPv6 properly, but let's make sure
                            # by setting up the connection with explicit IPv6 support
                            
                    except Exception as e:
                        print(f"  DNS resolution error: {e}")
                
                # Create the client with our configuration
                try:
                    _chroma_client = chromadb.HttpClient(**client_kwargs)
                    print("Successfully connected to ChromaDB")
                except Exception as e:
                    print(f"Failed to connect to ChromaDB: {e}")
                    # If it's an IPv6 connection issue, provide helpful information
                    if "Connection refused" in str(e) and args.host and '.railway.internal' in args.host:
                        print("  This might be an IPv6 connectivity issue.")
                        print("  Ensure ChromaDB is listening on :: (IPv6) not 0.0.0.0 (IPv4)")
                    raise
            except ssl.SSLError as e:
                print(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                print(f"Error connecting to HTTP client: {str(e)}")
                raise
            
        elif args.client_type == 'cloud':
            if not args.tenant:
                raise ValueError("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
            if not args.database:
                raise ValueError("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
            if not args.api_key:
                raise ValueError("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")
            
            try:
                _chroma_client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    ssl=True,  # Always use SSL for cloud
                    tenant=args.tenant,
                    database=args.database,
                    headers={
                        'x-chroma-token': args.api_key
                    }
                )
            except ssl.SSLError as e:
                print(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                print(f"Error connecting to cloud client: {str(e)}")
                raise
                
        elif args.client_type == 'persistent':
            if not args.data_dir:
                raise ValueError("Data directory must be provided via --data-dir flag when using persistent client")
            _chroma_client = chromadb.PersistentClient(path=args.data_dir)
        else:  # ephemeral
            _chroma_client = chromadb.EphemeralClient()
            
    return _chroma_client

def get_admin_client(args=None):
    """Get or create the global admin client instance."""
    global _admin_client, _current_tenant, _current_database
    
    if _admin_client is None:
        if args is None:
            parser = create_parser()
            args = parser.parse_args()
        
        # Load environment variables
        load_dotenv(dotenv_path=args.dotenv_path)
        
        if args.client_type == 'http':
            if not args.host:
                raise ValueError("Host must be provided for AdminClient")
            
            settings = Settings(
                chroma_api_impl="chromadb.api.fastapi.FastAPI",
                chroma_server_host=args.host,
                chroma_server_http_port=str(args.port) if args.port else "8000"
            )
            
            if args.custom_auth_credentials:
                settings.chroma_client_auth_provider = "chromadb.auth.basic_authn.BasicAuthClientProvider"
                settings.chroma_client_auth_credentials = args.custom_auth_credentials
            
            try:
                _admin_client = AdminClient(settings)
                print("Successfully created AdminClient")
            except Exception as e:
                print(f"Failed to create AdminClient: {e}")
                raise
        else:
            # For local/persistent clients, AdminClient might not be supported
            print("AdminClient is only supported for HTTP client type")
            return None
    
    # Set current context from args or use defaults
    if _current_tenant is None:
        _current_tenant = args.tenant if args and args.tenant else DEFAULT_TENANT
    if _current_database is None:
        _current_database = args.database if args and args.database else DEFAULT_DATABASE
    
    return _admin_client

##### Collection Tools #####

@mcp.tool()
async def chroma_list_collections(
    limit: int | None = None,
    offset: int | None = None
) -> List[str]:
    """List all collection names in the Chroma database with pagination support.
    
    Args:
        limit: Optional maximum number of collections to return
        offset: Optional number of collections to skip before returning results
    
    Returns:
        List of collection names or ["__NO_COLLECTIONS_FOUND__"] if database is empty
    """
    client = get_chroma_client()
    try:
        colls = client.list_collections(limit=limit, offset=offset)
        # Safe handling: If colls is None or empty, return a special marker
        if not colls:
            return ["__NO_COLLECTIONS_FOUND__"]
        # Otherwise iterate to get collection names
        return [coll.name for coll in colls]

    except Exception as e:
        raise Exception(f"Failed to list collections: {str(e)}") from e

mcp_known_embedding_functions: Dict[str, EmbeddingFunction] = {
    "default": DefaultEmbeddingFunction,
    "cohere": CohereEmbeddingFunction,
    "openai": OpenAIEmbeddingFunction,
    "jina": JinaEmbeddingFunction,
    "voyageai": VoyageAIEmbeddingFunction,
    "roboflow": RoboflowEmbeddingFunction,
}

def _register_custom_embedding_if_available():
    """Register custom embedding function if environment variables are available."""
    api_url = os.getenv('EMBEDDINGS_API_URL')
    model = os.getenv('EMBEDDING_MODEL')
    
    if api_url and model:
        mcp_known_embedding_functions["custom"] = CustomEmbeddingFunction

def _get_default_embedding_function():
    """Get the default embedding function, preferring custom if available."""
    if "custom" in mcp_known_embedding_functions:
        return "custom"
    return "default"
@mcp.tool()
async def chroma_create_collection(
    collection_name: str,
    embedding_function_name: str | None = None,
    metadata: Dict | None = None,
) -> str:
    """Create a new Chroma collection with configurable HNSW parameters.
    
    Args:
        collection_name: Name of the collection to create
        embedding_function_name: Name of the embedding function to use. Options: 'default', 'cohere', 'openai', 'jina', 'voyageai', 'roboflow', 'custom'. If not specified, will auto-select 'custom' if EMBEDDINGS_API_URL is set, otherwise 'default'.
        metadata: Optional metadata dict to add to the collection
    """
    client = get_chroma_client()
    
    # Auto-select embedding function if not specified
    if embedding_function_name is None:
        embedding_function_name = _get_default_embedding_function()
    
    if embedding_function_name not in mcp_known_embedding_functions:
        available_functions = list(mcp_known_embedding_functions.keys())
        raise ValueError(f"Unknown embedding function '{embedding_function_name}'. Available options: {available_functions}")
    
    embedding_function = mcp_known_embedding_functions[embedding_function_name]
    
    configuration=CreateCollectionConfiguration(
        embedding_function=embedding_function()
    )
    
    try:
        client.create_collection(
            name=collection_name,
            configuration=configuration,
            metadata=metadata
        )
        config_msg = f" with configuration: {configuration}"
        return f"Successfully created collection {collection_name}{config_msg}"
    except Exception as e:
        raise Exception(f"Failed to create collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_peek_collection(
    collection_name: str,
    limit: int = 5
) -> Dict:
    """Peek at documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to peek into
        limit: Number of documents to peek at
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        results = collection.peek(limit=limit)
        return results
    except Exception as e:
        raise Exception(f"Failed to peek collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_get_collection_info(collection_name: str) -> Dict:
    """Get information about a Chroma collection.
    
    Args:
        collection_name: Name of the collection to get info about
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        
        # Get collection count
        count = collection.count()
        
        # Peek at a few documents
        peek_results = collection.peek(limit=3)
        
        return {
            "name": collection_name,
            "count": count,
            "sample_documents": peek_results
        }
    except Exception as e:
        raise Exception(f"Failed to get collection info for '{collection_name}': {str(e)}") from e
    
@mcp.tool()
async def chroma_get_collection_count(collection_name: str) -> int:
    """Get the number of documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to count
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.count()
    except Exception as e:
        raise Exception(f"Failed to get collection count for '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_modify_collection(
    collection_name: str,
    new_name: str | None = None,
    new_metadata: Dict | None = None,
) -> str:
    """Modify a Chroma collection's name or metadata.
    
    Args:
        collection_name: Name of the collection to modify
        new_name: Optional new name for the collection
        new_metadata: Optional new metadata for the collection
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        collection.modify(name=new_name, metadata=new_metadata)
        
        modified_aspects = []
        if new_name:
            modified_aspects.append("name")
        if new_metadata:
            modified_aspects.append("metadata")
        
        return f"Successfully modified collection {collection_name}: updated {' and '.join(modified_aspects)}"
    except Exception as e:
        raise Exception(f"Failed to modify collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_delete_collection(collection_name: str) -> str:
    """Delete a Chroma collection.
    
    Args:
        collection_name: Name of the collection to delete
    """
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        return f"Successfully deleted collection {collection_name}"
    except Exception as e:
        raise Exception(f"Failed to delete collection '{collection_name}': {str(e)}") from e

##### Document Tools #####
@mcp.tool()
async def chroma_add_documents(
    collection_name: str,
    documents: List[str],
    ids: List[str],
    metadatas: List[Dict] | None = None
) -> str:
    """Add documents to a Chroma collection.
    
    Args:
        collection_name: Name of the collection to add documents to
        documents: List of text documents to add
        ids: List of IDs for the documents (required)
        metadatas: Optional list of metadata dictionaries for each document
    """
    if not documents:
        raise ValueError("The 'documents' list cannot be empty.")
    
    if not ids:
        raise ValueError("The 'ids' list is required and cannot be empty.")
    
    # Check if there are empty strings in the ids list
    if any(not id.strip() for id in ids):
        raise ValueError("IDs cannot be empty strings.")
    
    if len(ids) != len(documents):
        raise ValueError(f"Number of ids ({len(ids)}) must match number of documents ({len(documents)}).")

    client = get_chroma_client()
    try:
        collection = client.get_or_create_collection(collection_name)
        
        # Check for duplicate IDs
        existing_ids = collection.get(include=[])["ids"]
        duplicate_ids = [id for id in ids if id in existing_ids]
        
        if duplicate_ids:
            raise ValueError(
                f"The following IDs already exist in collection '{collection_name}': {duplicate_ids}. "
                f"Use 'chroma_update_documents' to update existing documents."
            )
        
        result = collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Check the return value
        if result and isinstance(result, dict):
            # If the return value is a dictionary, it may contain success information
            if 'success' in result and not result['success']:
                raise Exception(f"Failed to add documents: {result.get('error', 'Unknown error')}")
            
            # If the return value contains the actual number added
            if 'count' in result:
                return f"Successfully added {result['count']} documents to collection {collection_name}"
        
        # Default return
        return f"Successfully added {len(documents)} documents to collection {collection_name}, result is {result}"
    except Exception as e:
        raise Exception(f"Failed to add documents to collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_query_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Dict | None = None,
    where_document: Dict | None = None,
    include: List[str] = ["documents", "metadatas", "distances"]
) -> Dict:
    """Query documents from a Chroma collection with advanced filtering.
    
    Args:
        collection_name: Name of the collection to query
        query_texts: List of query texts to search for
        n_results: Number of results to return per query
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
        include: List of what to include in response. By default, this will include documents, metadatas, and distances.
    """
    if not query_texts:
        raise ValueError("The 'query_texts' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include
        )
    except Exception as e:
        raise Exception(f"Failed to query documents from collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_get_documents(
    collection_name: str,
    ids: List[str] | None = None,
    where: Dict | None = None,
    where_document: Dict | None = None,
    include: List[str] = ["documents", "metadatas"],
    limit: int | None = None,
    offset: int | None = None
) -> Dict:
    """Get documents from a Chroma collection with optional filtering.
    
    Args:
        collection_name: Name of the collection to get documents from
        ids: Optional list of document IDs to retrieve
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
        include: List of what to include in response. By default, this will include documents, and metadatas.
        limit: Optional maximum number of documents to return
        offset: Optional number of documents to skip before returning results
    
    Returns:
        Dictionary containing the matching documents, their IDs, and requested includes
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.get(
            ids=ids,
            where=where,
            where_document=where_document,
            include=include,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise Exception(f"Failed to get documents from collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_update_documents(
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]] | None = None,
    metadatas: List[Dict] | None = None,
    documents: List[str] | None = None
) -> str:
    """Update documents in a Chroma collection.

    Args:
        collection_name: Name of the collection to update documents in
        ids: List of document IDs to update (required)
        embeddings: Optional list of new embeddings for the documents.
                    Must match length of ids if provided.
        metadatas: Optional list of new metadata dictionaries for the documents.
                   Must match length of ids if provided.
        documents: Optional list of new text documents.
                   Must match length of ids if provided.

    Returns:
        A confirmation message indicating the number of documents updated.

    Raises:
        ValueError: If 'ids' is empty or if none of 'embeddings', 'metadatas',
                    or 'documents' are provided, or if the length of provided
                    update lists does not match the length of 'ids'.
        Exception: If the collection does not exist or if the update operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    if embeddings is None and metadatas is None and documents is None:
        raise ValueError(
            "At least one of 'embeddings', 'metadatas', or 'documents' "
            "must be provided for update."
        )

    # Ensure provided lists match the length of ids if they are not None
    if embeddings is not None and len(embeddings) != len(ids):
        raise ValueError("Length of 'embeddings' list must match length of 'ids' list.")
    if metadatas is not None and len(metadatas) != len(ids):
        raise ValueError("Length of 'metadatas' list must match length of 'ids' list.")
    if documents is not None and len(documents) != len(ids):
        raise ValueError("Length of 'documents' list must match length of 'ids' list.")


    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(
            f"Failed to get collection '{collection_name}': {str(e)}"
        ) from e

    # Prepare arguments for update, excluding None values at the top level
    update_args = {
        "ids": ids,
        "embeddings": embeddings,
        "metadatas": metadatas,
        "documents": documents,
    }
    kwargs = {k: v for k, v in update_args.items() if v is not None}

    try:
        collection.update(**kwargs)
        return (
            f"Successfully processed update request for {len(ids)} documents in "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to update documents in collection '{collection_name}': {str(e)}"
        ) from e

@mcp.tool()
async def chroma_delete_documents(
    collection_name: str,
    ids: List[str]
) -> str:
    """Delete documents from a Chroma collection.

    Args:
        collection_name: Name of the collection to delete documents from
        ids: List of document IDs to delete

    Returns:
        A confirmation message indicating the number of documents deleted.

    Raises:
        ValueError: If 'ids' is empty
        Exception: If the collection does not exist or if the delete operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(
            f"Failed to get collection '{collection_name}': {str(e)}"
        ) from e

    try:
        collection.delete(ids=ids)
        return (
            f"Successfully deleted {len(ids)} documents from "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to delete documents from collection '{collection_name}': {str(e)}"
        ) from e

##### Admin Tools #####

@mcp.tool()
async def chroma_list_databases(
    tenant: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Dict[str, str]]:
    """List all databases in a tenant.
    
    Args:
        tenant: Tenant name (uses current context if not provided)
        limit: Maximum number of databases to return
        offset: Number of databases to skip
    
    Returns:
        List of database information dictionaries
    """
    global _current_tenant
    
    admin_client = get_admin_client()
    if not admin_client:
        raise Exception("AdminClient not available (only supported for HTTP client)")
    
    tenant_name = tenant or _current_tenant or DEFAULT_TENANT
    
    try:
        databases = admin_client.list_databases(
            tenant=tenant_name,
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "name": db.name,
                "id": str(db.id),
                "tenant": tenant_name
            }
            for db in databases
        ]
    except Exception as e:
        raise Exception(f"Failed to list databases: {str(e)}") from e

@mcp.tool()
async def chroma_get_current_context() -> Dict[str, str]:
    """Get the current tenant and database context.
    
    Returns:
        Dictionary with current tenant and database
    """
    global _current_tenant, _current_database
    
    return {
        "tenant": _current_tenant or DEFAULT_TENANT,
        "database": _current_database or DEFAULT_DATABASE
    }

@mcp.tool()
async def chroma_switch_context(
    tenant: Optional[str] = None,
    database: Optional[str] = None
) -> Dict[str, str]:
    """Switch the current tenant and/or database context.
    
    Args:
        tenant: New tenant name (optional)
        database: New database name (optional)
    
    Returns:
        Dictionary with the new context
    """
    global _current_tenant, _current_database, _chroma_client
    
    # Update context
    if tenant is not None:
        _current_tenant = tenant
    if database is not None:
        _current_database = database
    
    # Clear the client so it gets recreated with new context
    _chroma_client = None
    
    return {
        "tenant": _current_tenant or DEFAULT_TENANT,
        "database": _current_database or DEFAULT_DATABASE
    }

@mcp.tool()
async def chroma_list_all_collections() -> Dict[str, List[str]]:
    """List all collections across all databases in the current tenant.
    
    Returns:
        Dictionary mapping database names to their collections
    """
    admin_client = get_admin_client()
    if not admin_client:
        raise Exception("AdminClient not available (only supported for HTTP client)")
    
    global _current_tenant
    tenant_name = _current_tenant or DEFAULT_TENANT
    
    try:
        # Get all databases
        databases = admin_client.list_databases(tenant=tenant_name)
        
        result = {}
        for db in databases:
            # Create a client for each database
            client = chromadb.HttpClient(
                host=admin_client.settings.chroma_server_host,
                port=int(admin_client.settings.chroma_server_http_port),
                ssl=admin_client.settings.chroma_server_ssl,
                tenant=tenant_name,
                database=db.name,
                settings=admin_client.settings
            )
            
            # List collections in this database
            collections = client.list_collections()
            result[db.name] = [col.name for col in collections] if collections else []
        
        return result
    except Exception as e:
        raise Exception(f"Failed to list all collections: {str(e)}") from e

def validate_thought_data(input_data: Dict) -> Dict:
    """Validate thought data structure."""
    if not input_data.get("sessionId"):
        raise ValueError("Invalid sessionId: must be provided")
    if not input_data.get("thought") or not isinstance(input_data.get("thought"), str):
        raise ValueError("Invalid thought: must be a string")
    if not input_data.get("thoughtNumber") or not isinstance(input_data.get("thoughtNumber"), int):
            raise ValueError("Invalid thoughtNumber: must be a number")
    if not input_data.get("totalThoughts") or not isinstance(input_data.get("totalThoughts"), int):
        raise ValueError("Invalid totalThoughts: must be a number")
    if not isinstance(input_data.get("nextThoughtNeeded"), bool):
        raise ValueError("Invalid nextThoughtNeeded: must be a boolean")
        
    return {
        "sessionId": input_data.get("sessionId"),
        "thought": input_data.get("thought"),
        "thoughtNumber": input_data.get("thoughtNumber"),
        "totalThoughts": input_data.get("totalThoughts"),
        "nextThoughtNeeded": input_data.get("nextThoughtNeeded"),
        "isRevision": input_data.get("isRevision"),
        "revisesThought": input_data.get("revisesThought"),
        "branchFromThought": input_data.get("branchFromThought"),
        "branchId": input_data.get("branchId"),
        "needsMoreThoughts": input_data.get("needsMoreThoughts"),
    }

def main():
    """Entry point for the Chroma MCP server."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
        # re-parse args to read the updated environment variables
        parser = create_parser()
        args = parser.parse_args()
    
    # Validate required arguments based on client type
    if args.client_type == 'http':
        if not args.host:
            parser.error("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
    
    elif args.client_type == 'cloud':
        if not args.tenant:
            parser.error("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
        if not args.database:
            parser.error("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
        if not args.api_key:
            parser.error("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")
    
    # Initialize client with parsed args
    try:
        get_chroma_client(args)
        print("Successfully initialized Chroma client")
    except Exception as e:
        print(f"Failed to initialize Chroma client: {str(e)}")
        raise
    
    # Initialize and run the server
    print("Starting MCP server")
    mcp.run(transport='stdio')
    
if __name__ == "__main__":
    main()
