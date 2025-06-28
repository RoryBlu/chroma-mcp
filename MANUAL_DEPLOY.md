# Manual Railway Deployment Steps

Since Railway CLI requires interactive login, here's how to deploy manually:

## Method 1: Railway Web Dashboard (Recommended)

### Step 1: Create New Project
1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account if needed
5. Select the `chroma-mcp` repository

### Step 2: Set Environment Variables
In the Railway dashboard, go to your project → **"Variables"** tab and add:

```
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=chroma-gjdq
CHROMA_PORT=8000
CHROMA_SSL=false
EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

### Step 3: Deploy
Railway will automatically build and deploy using your `Dockerfile`.

## Method 2: Interactive CLI

### Step 1: Login Interactively
```bash
railway login
```
This will open a browser for authentication.

### Step 2: Initialize and Deploy
```bash
# Initialize project
railway init

# Set environment variables
railway variables set CHROMA_CLIENT_TYPE=http
railway variables set CHROMA_HOST=chroma-gjdq
railway variables set CHROMA_PORT=8000
railway variables set CHROMA_SSL=false
railway variables set EMBEDDINGS_API_URL=https://embeddings-development.up.railway.app
railway variables set EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
railway variables set EMBEDDING_DIMENSION=768

# Deploy
railway up
```

## Method 3: GitHub Integration

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for Railway deployment with custom embeddings"
git push origin main
```

### Step 2: Deploy from GitHub
1. Go to Railway dashboard
2. Create new project from GitHub repo
3. Set environment variables as above
4. Automatic deployment on every push

## Expected Result

After deployment, you should see:
- ✅ Service running at a Railway URL like `https://chroma-mcp-production-xxxx.up.railway.app`
- ✅ Build logs showing successful Docker build
- ✅ Application logs showing Chroma MCP starting
- ✅ Connection to your external Chroma server (`chroma-gjdq:8000`)
- ✅ Custom embedding API integration working

## Verification

1. Check Railway dashboard shows service as "Running"
2. View logs for any errors
3. Test MCP functionality with your client
4. Verify custom embeddings are being used

## Your Token
(Keep this secure - it's already in this file now)