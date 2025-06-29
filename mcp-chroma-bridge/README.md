# MCP Chroma Bridge

This bridge allows Claude Desktop and Claude Code to connect to a remote Chroma MCP server running on Railway or any HTTP endpoint.

## Architecture

```
Claude Desktop/Code (stdio) <-> Bridge (HTTP) <-> Remote Chroma MCP Server
```

## Setup

1. **Install dependencies:**
   ```bash
   cd mcp-chroma-bridge
   pip install -r requirements.txt
   ```

2. **Configure for Claude Desktop:**
   
   Copy the configuration to Claude Desktop's config directory:
   ```bash
   # On macOS
   cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # On Windows
   # Copy to %APPDATA%\Claude\claude_desktop_config.json
   
   # On Linux
   # Copy to ~/.config/Claude/claude_desktop_config.json
   ```
   
   Or merge the "chroma-admin" section into your existing config.

3. **Update the configuration:**
   
   Edit the config file and update:
   - `remote-url`: Your Chroma MCP server URL
   - `auth-token`: Your authentication token (if required)

## Usage

### For Claude Desktop
Once configured, restart Claude Desktop. You should see "chroma-admin" in your MCP connections.

### For Claude Code
Add this to your project's `.claude.json`:
```json
{
  "mcpServers": {
    "chroma-admin": {
      "command": "python3",
      "args": [
        "/path/to/mcp_chroma_bridge.py",
        "--remote-url", "https://your-chroma-mcp.up.railway.app",
        "--auth-token", "your-auth-token"
      ]
    }
  }
}
```

### Testing
Run the test script to verify connectivity:
```bash
python test_bridge.py
```

## Available Tools

- `chroma_list_collections` - List all collections
- `chroma_create_collection` - Create a new collection
- `chroma_get_collection` - Get collection details
- `chroma_delete_collection` - Delete a collection
- `chroma_add_documents` - Add documents to a collection
- `chroma_query_collection` - Query/search documents
- `chroma_update_documents` - Update existing documents
- `chroma_delete_documents` - Delete documents

## Troubleshooting

1. **Check logs:**
   The bridge creates a `mcp-bridge.log` file with detailed information.

2. **Test connectivity:**
   ```bash
   curl https://your-chroma-mcp.up.railway.app/health
   ```

3. **Debug mode:**
   Add `--debug` flag for verbose logging:
   ```bash
   python mcp_chroma_bridge.py --remote-url URL --auth-token TOKEN --debug
   ```

## Security Notes

- The auth token is passed as a command-line argument, which may be visible in process lists
- Consider using environment variables or a config file for production use
- The bridge logs all operations for audit purposes