"""
HTTP wrapper for Chroma MCP Server
Provides HTTP endpoints that bridge to the MCP protocol
"""

import os
import json
import asyncio
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager
import argparse
from dotenv import load_dotenv

# Add the parent directory to the path to import server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
chroma_client = None
server_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ChromaDB client on startup"""
    global chroma_client, server_instance
    
    # Load environment variables
    load_dotenv()
    
    # Import server module
    from chroma_mcp.server import get_chroma_client, create_parser, mcp, main
    
    # Create args similar to command line
    parser = create_parser()
    args = parser.parse_args([])  # Use defaults and env vars
    
    # Initialize ChromaDB client
    try:
        chroma_client = get_chroma_client(args)
        logger.info("ChromaDB client initialized successfully")
        
        # Initialize the MCP server to register all tools
        server_instance = mcp
        
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB client: {e}")
        raise
    
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
            # Get tools from the MCP server
            tools = []
            if server_instance and hasattr(server_instance, '_tools'):
                for tool_name, tool_info in server_instance._tools.items():
                    tools.append({
                        "name": tool_name,
                        "description": tool_info.get('description', ''),
                        "inputSchema": tool_info.get('params_schema', {
                            "type": "object",
                            "properties": {},
                            "required": []
                        })
                    })
            else:
                # Fallback to hardcoded tools
                tools = get_tool_definitions()
            result = {"tools": tools}
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
        
        # Import the tool functions
        from chroma_mcp.server import (
            chroma_list_collections,
            chroma_create_collection,
            chroma_peek_collection,
            chroma_get_collection_info,
            chroma_get_collection_count,
            chroma_modify_collection,
            chroma_delete_collection,
            chroma_add_documents,
            chroma_query_documents,
            chroma_get_documents,
            chroma_update_documents,
            chroma_delete_documents,
            chroma_list_databases,
            chroma_get_current_context,
            chroma_switch_context,
            chroma_list_all_collections,
        )
        
        # Map tool names to functions
        tool_map = {
            "chroma_list_collections": lambda: chroma_list_collections(
                limit=params.get("limit"),
                offset=params.get("offset")
            ),
            "chroma_create_collection": lambda: chroma_create_collection(
                collection_name=params.get("collection_name"),
                embedding_function_name=params.get("embedding_function_name"),
                metadata=params.get("metadata")
            ),
            "chroma_peek_collection": lambda: chroma_peek_collection(
                collection_name=params.get("collection_name"),
                limit=params.get("limit", 5)
            ),
            "chroma_get_collection_info": lambda: chroma_get_collection_info(
                collection_name=params.get("collection_name")
            ),
            "chroma_get_collection_count": lambda: chroma_get_collection_count(
                collection_name=params.get("collection_name")
            ),
            "chroma_modify_collection": lambda: chroma_modify_collection(
                collection_name=params.get("collection_name"),
                new_name=params.get("new_name"),
                new_metadata=params.get("new_metadata")
            ),
            "chroma_delete_collection": lambda: chroma_delete_collection(
                collection_name=params.get("collection_name")
            ),
            "chroma_add_documents": lambda: chroma_add_documents(
                collection_name=params.get("collection_name"),
                documents=params.get("documents"),
                ids=params.get("ids"),
                metadatas=params.get("metadatas")
            ),
            "chroma_query_documents": lambda: chroma_query_documents(
                collection_name=params.get("collection_name"),
                query_texts=params.get("query_texts"),
                n_results=params.get("n_results", 10),
                where=params.get("where"),
                where_document=params.get("where_document"),
                include=params.get("include")
            ),
            "chroma_get_documents": lambda: chroma_get_documents(
                collection_name=params.get("collection_name"),
                ids=params.get("ids"),
                where=params.get("where"),
                limit=params.get("limit"),
                offset=params.get("offset"),
                where_document=params.get("where_document"),
                include=params.get("include")
            ),
            "chroma_update_documents": lambda: chroma_update_documents(
                collection_name=params.get("collection_name"),
                ids=params.get("ids"),
                documents=params.get("documents"),
                metadatas=params.get("metadatas")
            ),
            "chroma_delete_documents": lambda: chroma_delete_documents(
                collection_name=params.get("collection_name"),
                ids=params.get("ids")
            ),
            "chroma_list_databases": lambda: chroma_list_databases(
                tenant=params.get("tenant"),
                limit=params.get("limit"),
                offset=params.get("offset")
            ),
            "chroma_get_current_context": lambda: chroma_get_current_context(),
            "chroma_switch_context": lambda: chroma_switch_context(
                tenant=params.get("tenant"),
                database=params.get("database")
            ),
            "chroma_list_all_collections": lambda: chroma_list_all_collections(),
        }
        
        if tool_name not in tool_map:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
        
        # Execute the tool
        result = await tool_map[tool_name]()
        
        # Return raw result - the bridge will wrap it in JSON-RPC format
        return result
        
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
                "properties": {
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                },
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
            "name": "chroma_peek_collection",
            "description": "Peek at documents in a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["collection_name"]
            }
        },
        {
            "name": "chroma_get_collection_info",
            "description": "Get detailed information about a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"}
                },
                "required": ["collection_name"]
            }
        },
        {
            "name": "chroma_get_collection_count",
            "description": "Get the number of documents in a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"}
                },
                "required": ["collection_name"]
            }
        },
        {
            "name": "chroma_modify_collection",
            "description": "Modify a collection's name or metadata",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "new_name": {"type": "string"},
                    "new_metadata": {"type": "object"}
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
            "name": "chroma_query_documents",
            "description": "Query documents in a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "query_texts": {"type": "array", "items": {"type": "string"}},
                    "n_results": {"type": "integer"},
                    "where": {"type": "object"},
                    "where_document": {"type": "object"},
                    "include": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["collection_name", "query_texts"]
            }
        },
        {
            "name": "chroma_get_documents",
            "description": "Get documents from a collection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string"},
                    "ids": {"type": "array", "items": {"type": "string"}},
                    "where": {"type": "object"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"},
                    "where_document": {"type": "object"},
                    "include": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["collection_name"]
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
                    "ids": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["collection_name", "ids"]
            }
        },
        {
            "name": "chroma_list_databases",
            "description": "List all databases in a tenant",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tenant": {"type": "string"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                },
                "required": []
            }
        },
        {
            "name": "chroma_get_current_context",
            "description": "Get the current tenant and database context",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "chroma_switch_context",
            "description": "Switch the current tenant and/or database context",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tenant": {"type": "string"},
                    "database": {"type": "string"}
                },
                "required": []
            }
        },
        {
            "name": "chroma_list_all_collections",
            "description": "List all collections across all databases in the current tenant",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
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