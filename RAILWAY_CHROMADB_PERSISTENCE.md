# ChromaDB Persistence on Railway - Critical Fix

## Problem Identified

Your ChromaDB collections aren't showing up because Railway containers use **ephemeral storage by default**. When your container restarts or redeploys, all data is lost. This explains why your collections from sparkjar-crew are missing.

## Solution: Add Persistent Volume

### Step 1: Create and Attach Volume in Railway

1. Go to your ChromaDB service (`chroma-gjdq`) in Railway dashboard
2. Click on **Settings** → **Volumes**
3. Click **"Create Volume"**
4. Configure the volume:
   - **Name**: `chromadb-data`
   - **Mount Path**: `/chroma-data`
   - **Size**: 10GB (or larger based on your needs)
5. Click **"Create"**

### Step 2: Update Environment Variables

In your ChromaDB service settings, add/update these environment variables:

```bash
# Persistence Configuration
PERSIST_DIRECTORY=/chroma-data
IS_PERSISTENT=TRUE
ALLOW_RESET=FALSE

# Your existing variables
CHROMA_HOST=chroma-gjdq.railway.internal
CHROMA_PORT=8080
CHROMA_SSL=false
CHROMA_CUSTOM_AUTH_CREDENTIALS=gi9v25dw33k086falw1c1i5m55b2uynt
```

### Step 3: Update Dockerfile for Persistence

Create an updated Dockerfile that ensures proper permissions:

```dockerfile
# ChromaDB with IPv6 support and persistence for Railway
FROM ghcr.io/chroma-core/chroma:latest

# Create the persist directory with proper permissions
RUN mkdir -p /chroma-data && \
    chown -R 1000:1000 /chroma-data

# Set the persist directory
ENV PERSIST_DIRECTORY=/chroma-data
ENV IS_PERSISTENT=TRUE

# The ChromaDB image has ENTRYPOINT ["chroma"]
# We need to use the "run" subcommand with proper arguments
CMD ["run", "--host", "::", "--port", "8000", "--path", "/chroma-data"]
```

### Step 4: Verify Volume Mount

After deploying with the volume:

1. SSH into your Railway service (if available) or check logs
2. Verify the volume is mounted:
   ```bash
   ls -la /chroma-data
   ```
3. After creating collections, verify files exist:
   ```bash
   ls -la /chroma-data/
   # You should see chroma.sqlite3 and other persistence files
   ```

## Testing Persistence

### Quick Test Procedure

1. **Create a test collection**:
   ```python
   # Using the MCP bridge
   chroma_create_collection(collection_name="persistence_test")
   ```

2. **Add some data**:
   ```python
   chroma_add_documents(
       collection_name="persistence_test",
       documents=["Test document 1", "Test document 2"],
       ids=["test1", "test2"]
   )
   ```

3. **Manually trigger a redeploy** in Railway dashboard

4. **Check if collection persists**:
   ```python
   chroma_list_collections()
   # Should show ["persistence_test"] instead of ["__NO_COLLECTIONS_FOUND__"]
   ```

## Data Recovery Options

Unfortunately, if your previous collections were stored in ephemeral storage, they're likely lost. However, you can:

1. **Check sparkjar-crew**: If the original application still has the data, you might be able to re-export it
2. **Look for backups**: Check if you have any ChromaDB exports or backups
3. **Recreate from source**: If you still have the original documents, you can re-index them

## Important Notes

1. **Volume Costs**: Railway charges for persistent volumes based on size and usage
2. **Backup Strategy**: Consider implementing regular backups of `/chroma-data`
3. **Multiple Instances**: Ensure all ChromaDB instances share the same volume if you need data consistency
4. **Migration**: When moving between services, always export/import your collections

## Monitoring Persistence

Add these checks to your deployment:

1. **Health check endpoint** that verifies persistence directory exists
2. **Collection count metric** to monitor data presence
3. **Disk usage alerts** to prevent volume from filling up

## Next Steps

1. Implement the volume immediately to prevent further data loss
2. Test persistence with a small collection
3. Re-import your important data from sparkjar-crew or other sources
4. Set up automated backups for the persistent volume

The lack of persistent storage is the root cause. Once you add the volume and configure the persist directory, your ChromaDB data will survive container restarts and redeploys.