# Instructions: Replace ChromaDB with IPv6-Enabled Version on Railway

Follow these steps to replace your existing ChromaDB deployment with the IPv6-enabled version.

## Step 1: Disconnect Current ChromaDB Image

1. Go to your Railway dashboard
2. Click on your **Chroma-GjDQ** service
3. Go to the **Settings** tab
4. In the **Source** section, click the **Disconnect** button next to `ghcr.io/chroma-core/chroma:latest`

## Step 2: Connect to GitHub Repository

1. After disconnecting, you'll see options to connect a new source
2. Click **"GitHub Repo"**
3. Select your repository: **RoryBlu/chroma-mcp**
4. Railway will ask for the branch - select **main**

## Step 3: Configure Build Settings

1. Once connected, Railway needs to know what to build
2. In the **Build Configuration** section:
   - **Root Directory**: Set to `chromadb-ipv6`
   - **Dockerfile Path**: Set to `Dockerfile.simple`
   - Leave other settings as default

## Step 4: Environment Variables

Your existing environment variables should remain:
- Any persistence settings (PERSIST_DIRECTORY, etc.)
- Any other ChromaDB configurations

No changes needed here!

## Step 5: Deploy

1. Click **"Deploy"** or Railway will auto-deploy after configuration
2. Watch the build logs to ensure it builds successfully
3. The new image will:
   - Use the official ChromaDB as base
   - Modify it to listen on IPv6 interfaces
   - Enable dual-stack (IPv4 + IPv6) support

## Step 6: Verify After Deployment

Once deployed, your ChromaDB logs should show:
```
INFO:     Uvicorn running on http://[::]:8000 (Press CTRL+C to quit)
```

Instead of:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Step 7: Test Your Chroma MCP Connection

Your Chroma MCP service should now connect successfully with:
```
CHROMA_HOST=chroma-gjdq.railway.internal
CHROMA_PORT=8000
CHROMA_SSL=false
```

## Troubleshooting

If the simple Dockerfile doesn't work:
1. Change **Dockerfile Path** to just `Dockerfile` (without .simple)
2. This uses the more complex socat-based solution
3. Redeploy and test again

## Alternative: If GitHub Build Doesn't Work

If you prefer using a pre-built image:
1. Build locally: `docker build -f Dockerfile.simple -t yourdockerhub/chromadb-ipv6:latest chromadb-ipv6/`
2. Push to Docker Hub: `docker push yourdockerhub/chromadb-ipv6:latest`
3. In Railway, use "Docker Image" source instead
4. Enter: `yourdockerhub/chromadb-ipv6:latest`

## Benefits of This Approach

- Your data remains intact (using same volumes)
- All environment variables stay the same
- Only the networking layer changes
- Automatic rebuilds when you push updates to GitHub
- No external Docker Hub dependency

The key change is that ChromaDB will now listen on both IPv4 and IPv6, enabling Railway's private networking to work correctly!