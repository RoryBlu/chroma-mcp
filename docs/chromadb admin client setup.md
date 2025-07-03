# ChromaDB AdminClient Setup Guide

## Overview

ChromaDB's AdminClient provides advanced functionality for managing multiple tenants and databases. However, it requires specific server configuration that isn't enabled in the default ChromaDB setup. This guide explains how to properly configure ChromaDB to support AdminClient operations.

## Prerequisites

- ChromaDB server (not just the client library)
- Docker (recommended) or Python environment
- Basic understanding of ChromaDB concepts (tenants, databases, collections)

## Understanding the Architecture

### Default ChromaDB Setup
```
ChromaDB Client → Single Database → Collections
```

### Multi-tenant ChromaDB Setup
```
AdminClient → Tenants → Databases → Collections
```

## Server Configuration Requirements

### 1. Running ChromaDB Server with Multi-tenant Support

ChromaDB server must be started with specific flags to enable AdminClient functionality:

#### Using Docker (Recommended)

```bash
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -e CHROMA_SERVER_AUTH_PROVIDER="chromadb.auth.basic_authn.BasicAuthenticationServerProvider" \
  -e CHROMA_SERVER_AUTH_CREDENTIALS="admin:password" \
  -e CHROMA_SERVER_AUTH_TOKEN_TRANSPORT_HEADER="AUTHORIZATION" \
  -e ALLOW_RESET=TRUE \
  -e IS_PERSISTENT=TRUE \
  -v ./chroma-data:/chroma/chroma \
  chromadb/chroma:latest \
  --workers 1 \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --log-config chromadb/log_config.yml \
  --timeout-keep-alive 30
```

#### Using Python

```bash
# Install ChromaDB server
pip install chromadb

# Run with multi-tenant configuration
chroma run \
  --path ./chroma-data \
  --host 0.0.0.0 \
  --port 8000 \
  --allow-reset \
  --auth-provider chromadb.auth.basic_authn.BasicAuthenticationServerProvider \
  --auth-credentials admin:password
```

### 2. Environment Variables for Multi-tenant Mode

Set these environment variables before starting the ChromaDB server:

```bash
# Enable authentication (required for AdminClient)
export CHROMA_SERVER_AUTH_PROVIDER="chromadb.auth.basic_authn.BasicAuthenticationServerProvider"
export CHROMA_SERVER_AUTH_CREDENTIALS="admin:password"

# Enable persistence
export IS_PERSISTENT=TRUE
export PERSIST_DIRECTORY="./chroma-data"

# Allow database operations
export ALLOW_RESET=TRUE
```

### 3. Server Configuration File

Create a `chroma-config.yaml`:

```yaml
# ChromaDB Server Configuration
server:
  host: 0.0.0.0
  port: 8000
  
auth:
  provider: chromadb.auth.basic_authn.BasicAuthenticationServerProvider
  credentials: admin:password
  
persistence:
  enabled: true
  directory: ./chroma-data
  
tenancy:
  enabled: true
  default_tenant: default_tenant
  
database:
  default_database: default_database
  allow_reset: true
```

## Client Configuration

### 1. Connecting with AdminClient

```python
from chromadb.admin import AdminClient
from chromadb.config import Settings

# Configure settings for AdminClient
settings = Settings(
    chroma_server_host="localhost",
    chroma_server_http_port="8000",
    chroma_server_auth_credentials="admin:password",
    chroma_server_auth_provider="chromadb.auth.basic_authn.BasicAuthenticationServerProvider"
)

# Create AdminClient
admin = AdminClient(settings)

# List all databases
databases = admin.list_databases()
```

### 2. Environment Variables for Chroma MCP

When using Chroma MCP with AdminClient support:

```bash
# Required for AdminClient
export CHROMA_CLIENT_TYPE="http"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8000"
export CHROMA_CUSTOM_AUTH_CREDENTIALS="admin:password"

# Optional
export CHROMA_TENANT="default_tenant"
export CHROMA_DATABASE="default_database"
export CHROMA_SSL="false"
```

## Verifying AdminClient Setup

### 1. Test AdminClient Connection

```python
# Test script
from chromadb.admin import AdminClient
from chromadb.config import Settings

try:
    settings = Settings(
        chroma_server_host="localhost",
        chroma_server_http_port="8000",
        chroma_server_auth_credentials="admin:password"
    )
    
    admin = AdminClient(settings)
    
    # Test operations
    print("Tenants:", admin.list_tenants())
    print("Databases:", admin.list_databases())
    
    print("✅ AdminClient is working!")
    
except Exception as e:
    print(f"❌ AdminClient failed: {e}")
```

### 2. Using Chroma MCP Admin Tools

Once properly configured, you can use:

```bash
# List all databases
mcp-chroma list-databases

# Create a new database
mcp-chroma create-database --database "my_new_db"

# Delete a database
mcp-chroma delete-database --database "old_db"
```

## Common Issues and Solutions

### Issue 1: "AdminClient not available"

**Cause**: Server not configured for multi-tenant mode

**Solution**: Ensure ChromaDB server is started with auth provider and credentials

### Issue 2: "Connection refused"

**Cause**: Server not running or wrong host/port

**Solution**: 
- Check server is running: `docker ps` or `ps aux | grep chroma`
- Verify host and port settings
- Check firewall rules

### Issue 3: "Authentication failed"

**Cause**: Wrong credentials or auth not enabled

**Solution**:
- Verify CHROMA_SERVER_AUTH_CREDENTIALS matches server config
- Ensure auth provider is enabled on server
- Check credentials format (username:password)

### Issue 4: "Method not allowed"

**Cause**: Server running in single-tenant mode

**Solution**: Restart server with multi-tenant configuration flags

## Railway Deployment Considerations

For Railway deployments, AdminClient typically won't work because:

1. **Internal networking**: Railway uses IPv6 internal addresses
2. **Authentication**: Railway ChromaDB instances may not have auth enabled
3. **Configuration**: Can't modify server startup flags

### Workaround for Railway

Use environment variables to gracefully handle AdminClient absence:

```bash
# In your Railway service
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=chroma-service.railway.internal
CHROMA_PORT=8000
# AdminClient operations will fallback gracefully
```

## Security Best Practices

1. **Change default credentials**: Never use `admin:password` in production
2. **Use environment variables**: Don't hardcode credentials
3. **Enable SSL/TLS**: Use HTTPS in production
4. **Limit network access**: Use firewalls or VPCs
5. **Regular backups**: Backup the persist directory

## Testing AdminClient Features

### Create Test Script

```python
# test_admin.py
import os
from chromadb.admin import AdminClient
from chromadb.config import Settings

def test_admin_operations():
    settings = Settings(
        chroma_server_host=os.getenv("CHROMA_HOST", "localhost"),
        chroma_server_http_port=os.getenv("CHROMA_PORT", "8000"),
        chroma_server_auth_credentials=os.getenv("CHROMA_CUSTOM_AUTH_CREDENTIALS")
    )
    
    try:
        admin = AdminClient(settings)
        
        # List databases
        print("Current databases:")
        for db in admin.list_databases():
            print(f"  - {db.name} (tenant: {db.tenant})")
        
        # Create test database
        admin.create_database("test_db")
        print("✅ Created test_db")
        
        # List again
        print("\nDatabases after creation:")
        for db in admin.list_databases():
            print(f"  - {db.name}")
        
        # Clean up
        admin.delete_database("test_db")
        print("✅ Deleted test_db")
        
    except Exception as e:
        print(f"❌ Admin operations failed: {e}")
        print("\nMake sure ChromaDB server is configured for multi-tenant mode")

if __name__ == "__main__":
    test_admin_operations()
```

## Conclusion

AdminClient provides powerful multi-tenant capabilities but requires proper server configuration. The key is starting ChromaDB server with:

1. Authentication enabled
2. Persistence enabled  
3. Multi-tenant mode active
4. Proper credentials

For deployments where you can't control server configuration (like managed services), the Chroma MCP admin functions will gracefully fallback to showing current database information only.