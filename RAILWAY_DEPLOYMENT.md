# Railway Deployment Guide for Chroma MCP

This guide will help you deploy Chroma MCP with custom embedding support to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Railway CLI** (optional but recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   ```
3. **Git Repository**: Your code should be in a Git repository

## Method 1: Deploy via Railway Web Dashboard (Recommended)

### Step 1: Create New Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account if not already connected
5. Select this repository (`chroma-mcp`)

### Step 2: Configure Environment Variables

In the Railway dashboard, go to your project and click **"Variables"**:

#### Required Variables for Chroma MCP:
```bash
# Chroma Configuration
CHROMA_CLIENT_TYPE=ephemeral

# Custom Embedding API (your Railway embedding service)
EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

#### NOT Optional Variables (we ARE using external Chroma server):
# For HTTP client (connecting to remote Chroma)
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=chroma-gjdq
CHROMA_PORT=8000
CHROMA_SSL=false

### Step 3: Deploy

1. Railway will automatically detect the `Dockerfile` and start building
2. The build process will:
   - Install dependencies from `pyproject.toml`
   - Copy your application code
   - Set up the environment
3. Once deployed, you'll get a public URL like: `https://your-app-name.up.railway.app`

### Step 4: Test Your Deployment

You can test your deployment using the Railway-provided URL:

```bash
# Test with curl (if your server exposes HTTP endpoints)
curl https://your-app-name.up.railway.app/health

# Or test via MCP client tools
```

## Method 2: Deploy via Railway CLI

### Step 1: Initialize Railway Project

```bash
# In your project directory
railway login
railway init
```

### Step 2: Set Environment Variables

```bash
# Set required variables
railway variables set CHROMA_CLIENT_TYPE=http
railway variables set EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
railway variables set EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
railway variables set EMBEDDING_DIMENSION=768

# Optional: Set other variables as needed
railway variables set CHROMA_HOST=chroma-gjdq
railway variables set CHROMA_PORT=8000
```

### Step 3: Deploy

```bash
railway up
```

## Method 3: Deploy via GitHub Integration

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Add Railway deployment support"
git push origin main
```

### Step 2: Connect Repository

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository
4. Railway will automatically deploy on every push to main

## Configuration Options

#### HTTP (Connect to External Chroma Server)
```bash
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=chroma-gjdq
CHROMA_PORT=8000
CHROMA_SSL=false
```
- ✅ Persistent data
- ✅ Scalable
- 💰 Requires external Chroma server

### Custom Embedding Configuration

Your custom embedding API should be running and accessible. The variables are:

```bash
# Required
EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

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

3. **Connection Issues**
   - Verify `CHROMA_HOST` and `CHROMA_PORT` if using HTTP client
   - Check SSL settings (`CHROMA_SSL=true/false`)
   - Ensure your external services are accessible from Railway

### Railway-Specific Considerations

1. **Storage**: Railway has ephemeral storage - use external databases for persistence
2. **Networking**: All outbound connections are allowed
3. **Memory**: Default limit is 512MB, upgrade if needed
4. **Environment Variables**: Set via dashboard or CLI, not in code

### Monitoring

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

- [ ] Environment variables configured
- [ ] Custom embedding API is running and accessible
- [ ] Health checks are working
- [ ] Monitoring is set up
- [ ] Custom domain configured (if needed)
- [ ] Resource limits appropriate for your workload
- [ ] Backup strategy for data (if using external storage)

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Chroma MCP Issues**: Create an issue in this repository

## Next Steps

After deployment:
1. Test all embedding functions work correctly
2. Monitor resource usage and adjust limits if needed
3. Set up monitoring and alerting
4. Consider setting up CI/CD for automatic deployments

Your Chroma MCP with custom embedding support is now running on Railway! 🚀