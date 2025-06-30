#!/usr/bin/env python3
"""
MCP Chroma Bridge - Stdio to HTTP proxy for Chroma MCP Server
Allows Claude Desktop and Claude Code to connect to remote Chroma MCP servers
"""

import asyncio
import json
import sys
import argparse
import logging
from typing import Any, Dict, Optional
import httpx
from contextlib import asynccontextmanager

# Configure logging
import os
log_file = os.path.join(os.path.expanduser('~'), '.mcp-bridge.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class MCPChromaBridge:
    """Bridge between stdio MCP protocol and HTTP MCP protocol"""
    
    def __init__(self, remote_url: str, auth_token: Optional[str] = None):
        self.remote_url = remote_url.rstrip('/')
        self.auth_token = auth_token
        self.client = None
        
    async def start(self):
        """Start the bridge server"""
        logger.info(f"Starting MCP Chroma Bridge connecting to {self.remote_url}")
        
        # Initialize HTTP client with longer timeout for Railway
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=self._get_headers()
        )
        
        # Don't send initialization - wait for Claude to initialize
        logger.info("Bridge ready, waiting for initialization from Claude...")
        
        # Start processing messages
        await self._process_messages()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers including auth if provided"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
        
    async def _send_message(self, message: Dict[str, Any]):
        """Send a message to stdout"""
        output = json.dumps(message) + "\n"
        sys.stdout.write(output)
        sys.stdout.flush()
        logger.info(f"Sent: {message}")
        
    async def _read_message(self) -> Optional[Dict[str, Any]]:
        """Read a message from stdin"""
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                return None
            message = json.loads(line.strip())
            logger.info(f"Received: {message}")
            return message
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            return None
            
    async def _forward_to_remote(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Forward a message to the remote MCP server"""
        try:
            # For tool calls, we need to properly structure the request
            if message.get("method") == "tools/call":
                tool_name = message["params"]["name"]
                tool_args = message["params"].get("arguments", {})
                
                # Map to Chroma MCP's HTTP API format
                if tool_name.startswith("chroma_"):
                    endpoint = f"/tools/{tool_name}"
                    response = await self.client.post(
                        f"{self.remote_url}{endpoint}",
                        json=tool_args
                    )
                else:
                    # Unknown tool
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        },
                        "id": message.get("id")
                    }
            else:
                # For other methods, forward as-is
                response = await self.client.post(
                    f"{self.remote_url}/mcp",
                    json=message
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Ensure proper JSON-RPC response format
            if "jsonrpc" not in result:
                # For tool calls, wrap the result in content format expected by MCP
                if message.get("method") == "tools/call":
                    result = {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result) if not isinstance(result, str) else result
                                }
                            ]
                        },
                        "id": message.get("id")
                    }
                else:
                    result = {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": message.get("id")
                    }
                
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from remote: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Remote server error: {e.response.status_code}",
                    "data": e.response.text
                },
                "id": message.get("id")
            }
        except Exception as e:
            logger.error(f"Error forwarding to remote: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": message.get("id")
            }
            
    async def _process_messages(self):
        """Main message processing loop"""
        try:
            while True:
                message = await self._read_message()
                if message is None:
                    logger.info("No more messages, exiting...")
                    break
                    
                logger.info(f"Processing message: {message}")
                
                # Handle special cases locally
                if message.get("method") == "initialize":
                    # Respond with the protocol version Claude Desktop expects
                    protocol_version = message.get("params", {}).get("protocolVersion", "2024-11-05")
                    await self._send_message({
                        "jsonrpc": "2.0",
                        "result": {
                            "protocolVersion": protocol_version,
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "mcp-chroma-bridge",
                                "version": "1.0.0"
                            }
                        },
                        "id": message.get("id")
                    })
                elif message.get("method") == "tools/list":
                    # Get tool list from remote
                    tools = await self._get_remote_tools()
                    await self._send_message({
                        "jsonrpc": "2.0",
                        "result": {"tools": tools},
                        "id": message.get("id")
                    })
                else:
                    # Forward everything else
                    response = await self._forward_to_remote(message)
                    await self._send_message(response)
        except Exception as e:
            logger.error(f"Error in message processing: {e}", exc_info=True)
                
    async def _get_remote_tools(self) -> list:
        """Get the list of available tools from remote server"""
        try:
            # Try to get tools from the remote server
            response = await self.client.get(f"{self.remote_url}/tools")
            response.raise_for_status()
            tools_data = response.json()
            
            # Convert to MCP format if needed
            if isinstance(tools_data, dict) and "tools" in tools_data:
                return tools_data["tools"]
            elif isinstance(tools_data, list):
                return tools_data
            else:
                # Fallback to known Chroma MCP tools
                return self._get_default_tools()
                
        except Exception as e:
            logger.warning(f"Failed to get tools from remote: {e}")
            return self._get_default_tools()
            
    def _get_default_tools(self) -> list:
        """Return default Chroma MCP tools"""
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
            }
        ]
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()
            

async def main():
    parser = argparse.ArgumentParser(description="MCP Chroma Bridge - Stdio to HTTP proxy")
    parser.add_argument("--remote-url", required=True, help="Remote Chroma MCP server URL")
    parser.add_argument("--auth-token", help="Authentication token for remote server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    bridge = MCPChromaBridge(args.remote_url, args.auth_token)
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Bridge shutting down...")
    except Exception as e:
        logger.error(f"Bridge error: {e}")
    finally:
        await bridge.cleanup()
        

if __name__ == "__main__":
    asyncio.run(main())