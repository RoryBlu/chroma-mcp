# Quick Deploy Instructions

## Option 1: Automated Deployment (Recommended)

### Step 1: Get Railway API Token
1. Go to [railway.app/account/tokens](https://railway.app/account/tokens)
2. Click **"Create Token"**
3. Give it a name like "Chroma MCP Deploy"
4. Copy the token (it starts with something like `railway_live_...`)

### Step 2: Set Environment Variable
```bash
export RAILWAY_TOKEN=your_token_here
```

### Step 3: Run Deployment Script
```bash
./deploy_to_railway.sh
```

## Option 2: Manual Deployment

### Step 1: Login to Railway
```bash
railway login
```

### Step 2: Initialize Project
```bash
railway init
```

### Step 3: Set Environment Variables
```bash
# Chroma Configuration (HTTP client to external server)
railway variables set CHROMA_CLIENT_TYPE=http
railway variables set CHROMA_HOST=chroma-gjdq
railway variables set CHROMA_PORT=8000
railway variables set CHROMA_SSL=false

# Custom Embedding API Configuration
railway variables set EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
railway variables set EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
railway variables set EMBEDDING_DIMENSION=768
```

### Step 4: Deploy
```bash
railway up
```

## Expected Output

After deployment, you should see:
- Build logs showing Docker build process
- Service starting with your custom embedding configuration
- A Railway URL like `https://chroma-mcp-production.up.railway.app`

## Verification

Once deployed, you can verify it's working by checking:
1. Railway dashboard shows service as "Running"
2. Logs show no errors
3. Custom embedding API is being used for vector operations

## Environment Variables Set

The deployment will configure:
- `CHROMA_CLIENT_TYPE=http` - Connect to external Chroma server
- `CHROMA_HOST=chroma-gjdq` - Your Chroma server hostname
- `CHROMA_PORT=8000` - Chroma server port
- `CHROMA_SSL=false` - No SSL for internal connections
- `EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app` - Your custom embedding service
- `EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base` - Embedding model to use
- `EMBEDDING_DIMENSION=768` - Vector dimension size