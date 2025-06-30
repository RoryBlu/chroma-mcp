# Railway Deployment Guide for Chroma MCP with Custom Embeddings

This comprehensive guide will help you deploy Chroma MCP with custom embedding support to Railway.

## Overview

Chroma MCP now includes built-in support for custom embedding APIs as part of its base configuration. This means you can use your own embedding service without API keys, perfect for open-source deployments and privacy-conscious applications.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Railway CLI** (optional but recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   ```
3. **Git Repository**: Your code should be in a Git repository
4. **Custom Embedding Service**: Your embedding API should be running and accessible

## Quick Deploy

### Option 1: Automated Deployment Script

#### Step 1: Get Railway API Token
1. Go to [railway.app/account/tokens](https://railway.app/account/tokens)
2. Click **"Create Token"**
3. Give it a name like "Chroma MCP Deploy"
4. Copy the token (it starts with something like `railway_live_...`)

#### Step 2: Set Token and Run Script
```bash
export RAILWAY_TOKEN=your_token_here
./deploy_to_railway.sh
```

### Option 2: Deploy via Railway Web Dashboard (Recommended)

#### Step 1: Create New Project
1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account if not already connected
5. Select the `chroma-mcp` repository

#### Step 2: Configure Environment Variables

**IMPORTANT: Railway Private Networking Setup**

Before setting environment variables, you MUST enable private networking:

1. **Enable Private Networking on your Chroma Server (chroma-gjdq):**
   - Go to your `chroma-gjdq` service in Railway
   - Click "Settings" → "Networking"
   - Enable "Private Networking"
   - Note the **exact hostname and port** shown (Railway assigns these)

2. **Enable Private Networking on your Chroma MCP service:**
   - Go to your Chroma MCP service
   - Click "Settings" → "Networking"
   - Enable "Private Networking"

3. **Set Environment Variables:**
   
   In the Railway dashboard, go to your Chroma MCP project and click **"Variables"**:

```bash
# Chroma Configuration (HTTP client to external server)
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=chroma-gjdq.railway.internal
CHROMA_PORT=8080
CHROMA_SSL=false

# Tenant and Database (IMPORTANT: Must match your existing data!)
# If you previously used sparkjar-crew or other tools, they may have used specific values
# Default ChromaDB uses: tenant="default_tenant", database="default_database"
CHROMA_TENANT=default_tenant
CHROMA_DATABASE=default_database

# Authentication (if your Chroma server has auth enabled)
CHROMA_CUSTOM_AUTH_CREDENTIALS=gi9v25dw33k086falw1c1i5m55b2uynt

# Custom Embedding API Configuration (Base Config)
EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

**Note:** The CHROMA_PORT must match what Railway shows in the Chroma server's private networking settings, NOT necessarily 8000!

#### Step 3: Deploy
Railway will automatically detect the `Dockerfile` and start building. The build process will:
- Install dependencies from `pyproject.toml`
- Copy your application code
- Set up the environment with custom embeddings
- Start the service

Once deployed, you'll get a public URL like: `https://your-app-name.up.railway.app`

### Option 3: Deploy via Railway CLI

#### Step 1: Login and Initialize
```bash
railway login
railway init
```

#### Step 2: Set Environment Variables

**First, check your Chroma server's private networking port in Railway dashboard!**

```bash
# Chroma Configuration
railway variables set CHROMA_CLIENT_TYPE=http
railway variables set CHROMA_HOST=chroma-gjdq.railway.internal
railway variables set CHROMA_PORT=<PORT_FROM_PRIVATE_NETWORKING>  # Check Railway dashboard!
railway variables set CHROMA_SSL=false

# Custom Embedding API Configuration
railway variables set EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
railway variables set EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
railway variables set EMBEDDING_DIMENSION=768
```

#### Step 3: Deploy
```bash
railway up
```

### Option 4: GitHub Integration (Auto-Deploy)

#### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for Railway deployment with custom embeddings"
git push origin main
```

#### Step 2: Connect Repository
1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository
4. Set environment variables as shown above
5. Railway will automatically deploy on every push to main

## Custom Embeddings Configuration

### How It Works

When the custom embedding environment variables are set, Chroma MCP will:
- ✅ Automatically register a "custom" embedding function
- ✅ Auto-select it as the default for new collections
- ✅ Handle all embedding operations transparently through your API
- ✅ Maintain full compatibility with existing embedding providers

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EMBEDDINGS_API_URL` | Yes | Full URL to your embedding service |
| `EMBEDDING_MODEL` | Yes | Model name to pass to your API |
| `EMBEDDING_DIMENSION` | No | Vector dimension (default: 768) |

### API Requirements

Your embedding API should follow the OpenAI-compatible format:

**Endpoint**: `POST {EMBEDDINGS_API_URL}/embeddings`

**Request**:
```json
{
  "model": "your-model-name",
  "input": ["text1", "text2", ...],
  "encoding_format": "float"
}
```

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.1, 0.2, ...],
      "index": 0
    }
  ],
  "model": "your-model-name",
  "usage": {
    "prompt_tokens": 123,
    "total_tokens": 123
  }
}
```

## Usage Examples

### Auto-Selection (Recommended)
```python
# Will automatically use custom embeddings if configured
await mcp.call_tool("chroma_create_collection", {
    "collection_name": "my_collection"
})
```

### Explicit Selection
```python
# Explicitly choose custom embeddings
await mcp.call_tool("chroma_create_collection", {
    "collection_name": "my_collection",
    "embedding_function_name": "custom"
})
```

### Fallback to Built-in Providers
```python
# Still works with existing providers
await mcp.call_tool("chroma_create_collection", {
    "collection_name": "my_collection", 
    "embedding_function_name": "openai"  # or "cohere", "default", etc.
})
```

## Verification and Testing

### Step 1: Check Deployment Status
1. Railway dashboard shows service as "Running"
2. View logs: `railway logs` or check dashboard
3. Verify no startup errors

### Step 2: Test Custom Embeddings
You can test your deployment using:

```bash
# Test with curl (if your server exposes HTTP endpoints)
curl https://your-app-name.up.railway.app/health

# Or test via MCP client tools
```

### Expected Result
After deployment, you should see:
- ✅ Service running at Railway URL
- ✅ Build logs showing successful Docker build
- ✅ Application logs showing Chroma MCP starting
- ✅ Connection to external Chroma server (`chroma-gjdq:8000`)
- ✅ Custom embedding API integration working

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that `pyproject.toml` is valid
   - Ensure all dependencies are compatible
   - Look at Railway build logs for specific errors

2. **Runtime Errors**
   - Check Railway logs: `railway logs`
   - Verify environment variables are set correctly
   - Ensure your embedding API is accessible

3. **Connection Issues (MOST COMMON)**
   
   **Railway Private Networking Issues:**
   - **"Connection refused" errors** usually mean incorrect port configuration
   - Go to your Chroma server service → Settings → Networking
   - Enable "Private Networking" if not already enabled
   - Use the **exact port shown in Private Networking settings** (NOT the application port!)
   - Example: If Railway shows port 5432 for private networking, use that, not 8000
   
   **Correct format:**
   ```bash
   CHROMA_HOST=chroma-gjdq.railway.internal
   CHROMA_PORT=<PORT_FROM_RAILWAY_PRIVATE_NETWORKING>  # NOT necessarily 8000!
   CHROMA_SSL=false
   ```
   
   **Common mistakes:**
   - Using port 8000 when Railway assigns a different internal port
   - Not enabling private networking on BOTH services
   - Using just the service name without `.railway.internal`
   - Services not in the same Railway project

4. **Custom Embedding Issues**
   - Check Environment Variables: Ensure `EMBEDDINGS_API_URL` and `EMBEDDING_MODEL` are set
   - Test API Connectivity: Make sure your embedding API is accessible
   - Verify Response Format: Ensure your API returns OpenAI-compatible responses
   - Check Dimensions: Verify the embedding dimension matches your configuration

### Railway-Specific Considerations

1. **Storage**: Railway has ephemeral storage - use external databases for persistence
2. **Networking**: All outbound connections are allowed
3. **Memory**: Default limit is 512MB, upgrade if needed
4. **Environment Variables**: Set via dashboard or CLI, not in code

## Benefits of Custom Embeddings

- 🚀 **No API Keys Required** - Perfect for open-source deployments
- 🔧 **DIY Friendly** - Use any embedding model you want
- 💰 **Cost Control** - Run your own embedding infrastructure
- 🔒 **Privacy** - Keep your data on your own servers
- ⚡ **Performance** - Optimize for your specific use case

## Monitoring

Railway provides built-in monitoring:
- **Logs**: `railway logs` or view in dashboard
- **Metrics**: CPU, memory, network usage in dashboard
- **Health Checks**: Configured in `railway.json`

## Advanced Configuration

### Custom Domains
1. In Railway dashboard, go to **"Settings"**
2. Click **"Domains"**
3. Add your custom domain
4. Configure DNS as instructed

### Scaling
1. Go to **"Settings"** → **"Resources"**
2. Adjust CPU and memory allocation
3. Railway automatically handles horizontal scaling

### Secrets Management
For sensitive data:
1. Use Railway's environment variables (encrypted at rest)
2. Never commit secrets to your repository
3. Use different values for different environments

## Production Checklist

- [ ] Environment variables configured (including custom embeddings)
- [ ] Custom embedding API is running and accessible
- [ ] Health checks are working
- [ ] Monitoring is set up
- [ ] Custom domain configured (if needed)
- [ ] Resource limits appropriate for your workload
- [ ] Backup strategy for data (if using external storage)
- [ ] Verified custom embeddings are being used correctly

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Chroma MCP Issues**: Create an issue in this repository

## Next Steps

After deployment:
1. Test all embedding functions work correctly with your custom API
2. Monitor resource usage and adjust limits if needed
3. Set up monitoring and alerting
4. Consider setting up CI/CD for automatic deployments

Your Chroma MCP with custom embedding support is now running on Railway! 🚀

The implementation includes comprehensive error handling and will provide clear error messages to help you debug any issues.