# Railway ChromaDB Multi-Tenant Migration Guide

## Current Setup Analysis

Your current ChromaDB deployment has:
- ✅ Authentication enabled (using TokenAuthenticationServerProvider)
- ✅ Persistence enabled (`IS_PERSISTENT="True"`)
- ✅ Custom auth token configured
- ❌ Multi-tenant mode not explicitly enabled
- ❌ `ALLOW_RESET` not set (required for database operations)

## Migration Steps

### Step 1: Update Railway Environment Variables

Add these environment variables to your Railway ChromaDB service:

```bash
# Keep existing variables
ANONYMIZED_TELEMETRY="False"
CHROMA_AUTH_TOKEN_TRANSPORT_HEADER="Authorization"
CHROMA_HOST_ADDR="0.0.0.0"
CHROMA_PRIVATE_URL="http://${{RAILWAY_PRIVATE_DOMAIN}}"
CHROMA_PUBLIC_URL="https://${{RAILWAY_PUBLIC_DOMAIN}}"
CHROMA_SERVER_AUTHN_CREDENTIALS="gi9v25dw33k086falw1c1i5m55b2uynt"
CHROMA_SERVER_AUTHN_PROVIDER="chromadb.auth.token_authn.TokenAuthenticationServerProvider"
CHROMA_TIMEOUT_KEEP_ALIVE="30"
CHROMA_WORKERS="1"
IS_PERSISTENT="True"

# Add these new variables for multi-tenant support
ALLOW_RESET="True"  # Required for database operations
CHROMA_MULTI_TENANT="True"  # Enable multi-tenant mode
CHROMA_DEFAULT_TENANT="default_tenant"
CHROMA_DEFAULT_DATABASE="default_database"
```

### Step 2: Check ChromaDB Docker Image

Look at your `chromadb-ipv6` Docker image. It needs to support multi-tenant mode. Check if it's based on:
- `chromadb/chroma:latest` (good - supports multi-tenant)
- Custom build (need to verify it includes multi-tenant support)

### Step 3: Update Dockerfile (if using custom image)

If `chromadb-ipv6` is a custom build, ensure the Dockerfile includes:

```dockerfile
FROM chromadb/chroma:latest

# Your IPv6 configurations...

# Ensure the server starts with multi-tenant support
CMD ["uvicorn", "chromadb.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--proxy-headers", \
     "--timeout-keep-alive", "30"]
```

### Step 4: Update Chroma MCP Configuration

Update your Chroma MCP environment variables to work with the token auth:

```bash
# For Chroma MCP service
CHROMA_CLIENT_TYPE="http"
CHROMA_HOST="chroma-gjdq.railway.internal"
CHROMA_PORT="8000"
CHROMA_SSL="false"
CHROMA_CUSTOM_AUTH_CREDENTIALS="gi9v25dw33k086falw1c1i5m55b2uynt"
CHROMA_TENANT="default_tenant"
CHROMA_DATABASE="default_database"

# The auth token needs to be passed differently for AdminClient
CHROMA_AUTH_TOKEN="gi9v25dw33k086falw1c1i5m55b2uynt"
```

### Step 5: Update AdminClient Connection Code

The current implementation assumes BasicAuth, but you're using TokenAuth. Update the `get_or_create_admin_client` function:

```python
def get_or_create_admin_client(args=None):
    """Get or create AdminClient, returns None if not available."""
    global _admin_client
    
    if _admin_client is not None:
        return _admin_client
    
    # AdminClient only works with HTTP client type
    if args is None:
        parser = create_parser()
        args = parser.parse_args([])
    
    if args.client_type != 'http':
        logger.debug("AdminClient only available for HTTP client type")
        return None
    
    if not args.host:
        logger.debug("AdminClient requires host to be specified")
        return None
    
    try:
        # AdminClient with Token Authentication
        settings = Settings()
        settings.chroma_server_host = args.host
        settings.chroma_server_http_port = str(args.port) if args.port else "8000"
        
        if args.ssl:
            settings.chroma_server_ssl_enabled = True
        
        # Token Authentication (your current setup)
        auth_token = args.custom_auth_credentials or os.getenv('CHROMA_AUTH_TOKEN')
        if auth_token:
            settings.chroma_client_auth_provider = "chromadb.auth.token_authn.TokenAuthClientProvider"
            settings.chroma_client_auth_credentials = auth_token
            settings.chroma_client_auth_token_transport_header = "Authorization"
        
        _admin_client = AdminClient(settings)
        logger.info("Successfully created AdminClient with token auth")
        return _admin_client
        
    except Exception as e:
        logger.warning(f"AdminClient not available: {e}")
        return None
```

### Step 6: Test Multi-Tenant Features

Create a test script to verify multi-tenant is working:

```python
# test_railway_multitenant.py
import os
from chromadb.admin import AdminClient
from chromadb.config import Settings

# Railway configuration
settings = Settings()
settings.chroma_server_host = "chroma-gjdq.railway.internal"
settings.chroma_server_http_port = "8000"
settings.chroma_client_auth_provider = "chromadb.auth.token_authn.TokenAuthClientProvider"
settings.chroma_client_auth_credentials = "gi9v25dw33k086falw1c1i5m55b2uynt"
settings.chroma_client_auth_token_transport_header = "Authorization"

try:
    admin = AdminClient(settings)
    
    # Test listing databases
    databases = admin.list_databases()
    print(f"✅ AdminClient connected! Found {len(databases)} databases")
    
    # Try creating a test database
    admin.create_database("test_multitenant_db")
    print("✅ Successfully created test database")
    
    # Clean up
    admin.delete_database("test_multitenant_db")
    print("✅ Successfully deleted test database")
    
except Exception as e:
    print(f"❌ Multi-tenant not working: {e}")
    print("\nThis might mean:")
    print("1. ChromaDB server doesn't have ALLOW_RESET=True")
    print("2. The Docker image doesn't support multi-tenant")
    print("3. Additional configuration is needed")
```

## Potential Issues with Railway

### 1. Docker Image Limitations
If `chromadb-ipv6` is a minimal build, it might not include multi-tenant support. You may need to:
- Use the official `chromadb/chroma:latest` image
- Or rebuild with full ChromaDB server capabilities

### 2. Persistence Volume
Ensure your Railway service has a persistent volume mounted:
- Mount path: `/chroma/chroma`
- This preserves data across deployments

### 3. IPv6 Considerations
Your custom Docker image handles IPv6. Ensure this doesn't conflict with multi-tenant mode.

## Rollback Plan

If multi-tenant causes issues:

1. Remove the new environment variables:
   - `ALLOW_RESET`
   - `CHROMA_MULTI_TENANT`

2. Redeploy the service

3. Your existing single-database setup will continue working

## Verification Steps

After deployment:

1. **Check logs** for any startup errors:
   ```
   railway logs
   ```

2. **Test with Chroma MCP**:
   ```bash
   # Should list databases (or show fallback message)
   chroma_list_databases
   ```

3. **Monitor for errors** in the first 24 hours

## Alternative: Gradual Migration

If you want to test without affecting production:

1. **Clone the ChromaDB service** in Railway
2. **Add multi-tenant variables** to the clone
3. **Test thoroughly** with the clone
4. **Switch over** when confident

## Next Steps

1. **Backup your data** before making changes
2. **Add the environment variables** listed above
3. **Update the AdminClient code** to use token auth
4. **Deploy and test** the changes
5. **Monitor logs** for any issues

The key challenge is ensuring your `chromadb-ipv6` Docker image supports multi-tenant mode. If it's a minimal build for IPv6 support only, you might need to create a new Dockerfile that combines IPv6 support with full ChromaDB server features.