"""
HTTP wrapper for Chroma MCP Server
Provides HTTP endpoints that bridge to the MCP protocol
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

# Import the MCP server components
from .server import (
    mcp,
    ChromaClientType,
    initialize_client,
    list_collections,
    get_collection,
    create_collection,
    delete_collection,
    add_documents,
    query_collection,
    update_documents,
    delete_documents,
    count_collection,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instance
chroma_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ChromaDB client on startup"""
    global chroma_client
    
    # Initialize ChromaDB client
    args = type('Args', (), {
        'client_type': os.getenv('CHROMA_CLIENT_TYPE', 'http'),
        'host': os.getenv('CHROMA_HOST', 'localhost'),
        'port': os.getenv('CHROMA_PORT', '8000'),
        'ssl': os.getenv('CHROMA_SSL', 'false').lower() == 'true',
        'auth_type': 'custom' if os.getenv('CHROMA_CUSTOM_AUTH_CREDENTIALS') else None,
        'auth_provider': None,
        'path': os.getenv('CHROMA_PATH'),
    })()
    
    chroma_client = initialize_client(args)
    logger.info("ChromaDB client initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down HTTP server")

# Create FastAPI app
app = FastAPI(
    title="Chroma MCP HTTP Server",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "chroma-mcp-http"}

@app.get("/health")
async def health():
    """Health check with ChromaDB connection status"""
    try:
        if chroma_client:
            # Test connection
            chroma_client.list_collections()
            return {"status": "healthy", "chromadb": "connected"}
        else:
            return {"status": "unhealthy", "chromadb": "not initialized"}
    except Exception as e:
        return {"status": "unhealthy", "chromadb": "error", "error": str(e)}

@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """Handle MCP protocol messages over HTTP"""
    try:
        message = await request.json()
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")
        
        # Route to appropriate handler
        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "chroma-mcp-http",
                    "version": "1.0.0"
                }
            }
        elif method == "tools/list":
            result = {"tools": get_tool_definitions()}
        elif method == "notifications/initialized":
            # Just acknowledge
            return JSONResponse(content={})
        elif method == "resources/list":
            result = {"resources": []}
        elif method == "prompts/list":
            result = {"prompts": []}
        else:
            raise HTTPException(status_code=404, detail=f"Method not found: {method}")
        
        # Return JSON-RPC response
        response = {
            "jsonrpc": "2.0",
            "result": result
        }
        if request_id is not None:
            response["id"] = request_id
            
        return response
        
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": message.get("id") if 'message' in locals() else None
        }

@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Execute a specific tool"""
    try:
        params = await request.json()
        
        # Map tool names to functions
        tool_map = {
            "chroma_list_collections": list_collections,
            "chroma_get_collection": lambda: get_collection(params.get("collection_name")),
            "chroma_create_collection": lambda: create_collection(
                params.get("collection_name"),
                params.get("embedding_function_name"),
                params.get("metadata")
            ),
            "chroma_delete_collection": lambda: delete_collection(params.get("collection_name")),
            "chroma_add_documents": lambda: add_documents(
                params.get("collection_name"),
                params.get("documents"),
                params.get("ids"),
                params.get("metadatas")
            ),
            "chroma_query_collection": lambda: query_collection(
                params.get("collection_name"),
                params.get("query_texts"),
                params.get("n_results"),
                params.get("where"),
                params.get("where_document")
            ),
            "chroma_update_documents": lambda: update_documents(
                params.get("collection_name"),
                params.get("ids"),
                params.get("documents"),
                params.get("metadatas")
            ),
            "chroma_delete_documents": lambda: delete_documents(
                params.get("collection_name"),
                params.get("ids"),
                params.get("where")
            ),
            "chroma_count_collection": lambda: count_collection(params.get("collection_name")),
        }
        
        if tool_name not in tool_map:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
        
        # Execute the tool
        result = tool_map[tool_name]()
        
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {"tools": get_tool_definitions()}

def get_tool_definitions():
    """Get tool definitions in MCP format"""
    return [
        {
            "name": "chroma_list_collections",
            "description": "List all collections in ChromaDB",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "chroma_create_collection",
            "description": "Create a new collection in ChromaDB",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "embedding_function_name": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["collection_name"]
            }
        },
        {
            "name": "chroma_get_collection",
            "description": "Get details about a specific collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"}
                },
                "required": ["collection_name"]
            }
        },
        {
            "name": "chroma_delete_collection",
            "description": "Delete a collection from ChromaDB",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"}
                },
                "required": ["collection_name"]
            }
        },
        {
            "name": "chroma_add_documents",
            "description": "Add documents to a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "documents": {"type": "array", "items": {"type": "string"}},
                    "ids": {"type": "array", "items": {"type": "string"}},
                    "metadatas": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["collection_name", "documents"]
            }
        },
        {
            "name": "chroma_query_collection",
            "description": "Query documents in a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "query_texts": {"type": "array", "items": {"type": "string"}},
                    "n_results": {"type": "integer"},
                    "where": {"type": "object"},
                    "where_document": {"type": "object"}
                },
                "required": ["collection_name", "query_texts"]
            }
        },
        {
            "name": "chroma_update_documents",
            "description": "Update documents in a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "ids": {"type": "array", "items": {"type": "string"}},
                    "documents": {"type": "array", "items": {"type": "string"}},
                    "metadatas": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["collection_name", "ids"]
            }
        },
        {
            "name": "chroma_delete_documents",
            "description": "Delete documents from a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "ids": {"type": "array", "items": {"type": "string"}},
                    "where": {"type": "object"}
                },
                "required": ["collection_name"]
            }
        },
        {
            "name": "chroma_count_collection",
            "description": "Count documents in a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"}
                },
                "required": ["collection_name"]
            }
        }
    ]

def main():
    """Run the HTTP server"""
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting HTTP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()