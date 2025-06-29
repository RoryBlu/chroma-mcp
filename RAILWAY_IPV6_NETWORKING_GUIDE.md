# Railway IPv6 Private Networking Guide

## Problem Summary
Railway's private networking uses IPv6 exclusively. Services that only bind to IPv4 (0.0.0.0 or 127.0.0.1) will fail with "Connection refused" errors when accessed via Railway's internal network.

## Key Discoveries

1. **Railway provides both IPv4 and IPv6 interfaces:**
   ```
   railnet0: flags=4291<UP,BROADCAST,RUNNING,NOARP,MULTICAST>
           inet 10.250.10.185  (IPv4 - for public access)
           inet6 fd12:1bad:f2b8:0:2000:70:15ea:9d9d  (IPv6 - for private networking)
   ```

2. **Railway's private networking format:**
   - Hostname: `service-name.railway.internal`
   - Uses IPv6 exclusively for internal communication
   - Port is usually the same as your service listens on (not a special Railway port)

3. **The "Connection refused" error means:**
   - The network path is working (Railway can find the service)
   - But the service isn't listening on the IPv6 interface

## Solution Approaches (In Order of Preference)

### 1. Minimal Approach - Environment Variables (Try First!)
Many services respect environment variables for binding addresses. Check if your service supports:
- `HOST`, `BIND`, `BIND_ADDRESS`, `LISTEN_ADDRESS`
- Service-specific vars like `CHROMA_HOST_ADDR`, `REDIS_BIND`, etc.

**Example Dockerfile:**
```dockerfile
FROM original-image:latest
ENV HOST=0.0.0.0
# or
ENV BIND_ADDRESS=0.0.0.0
```

### 2. Command Line Arguments
If the service accepts command-line arguments:
```dockerfile
FROM original-image:latest
CMD ["your-service", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Wrapper Script Approach
Create a wrapper script that starts your service with the correct binding:
```dockerfile
FROM original-image:latest

USER root
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'exec your-service --host 0.0.0.0 --port ${PORT:-8000}' >> /start.sh && \
    chmod +x /start.sh

USER originaluser
ENTRYPOINT []
CMD ["/start.sh"]
```

### 4. Configuration File Approach
Some services only read from config files:
```dockerfile
FROM original-image:latest

# Create or modify config file
RUN echo "bind: 0.0.0.0" > /etc/service/config.yml
# or
RUN sed -i 's/127.0.0.1/0.0.0.0/g' /etc/service/config.yml
```

## Common Service-Specific Solutions

### Node.js Applications
```javascript
// Instead of:
app.listen(3000, 'localhost', ...)
// Use:
app.listen(3000, '0.0.0.0', ...)
// Or better:
app.listen(process.env.PORT || 3000, '0.0.0.0', ...)
```

### Python/FastAPI/Uvicorn
```bash
# Instead of:
uvicorn app:app --host localhost
# Use:
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Redis
```dockerfile
FROM redis:latest
CMD ["redis-server", "--bind", "0.0.0.0", "--protected-mode", "no"]
```

### PostgreSQL
```dockerfile
FROM postgres:latest
# PostgreSQL needs special handling for IPv6
RUN echo "listen_addresses = '*'" >> /etc/postgresql/postgresql.conf
```

## Debugging Steps

1. **Check if your service started:**
   Look for "Listening on..." or similar messages in logs

2. **Verify binding address:**
   - Good: `Listening on 0.0.0.0:8000` or `:::8000`
   - Bad: `Listening on 127.0.0.1:8000` or `localhost:8000`

3. **Test from another Railway service:**
   ```bash
   # This should work if properly configured:
   curl http://service-name.railway.internal:8000
   ```

4. **Common environment variables to check:**
   - `PORT` - Railway sets this
   - `RAILWAY_PRIVATE_DOMAIN` - Your internal hostname
   - Your service's specific binding configuration

## Quick Checklist

- [ ] Service binds to `0.0.0.0` not `localhost` or `127.0.0.1`
- [ ] Using the correct port (check Railway logs)
- [ ] Private networking enabled on both services
- [ ] Services are in the same Railway project
- [ ] Using `.railway.internal` suffix for internal connections
- [ ] No firewall/iptables rules blocking connections

## Example: Document Service Fix

If your document service is like ChromaDB, try:

```dockerfile
# Minimal approach
FROM your-document-service:latest
ENV HOST=0.0.0.0
# or whatever env var your service uses
ENV DOCUMENT_SERVICE_BIND_ADDRESS=0.0.0.0
```

Then in your connecting service:
```
DOCUMENT_SERVICE_URL=http://document-service.railway.internal:8000
```

## Important Notes

1. **Don't use IPv6-specific addresses** like `::` or `::1`
   - Use `0.0.0.0` which binds to all interfaces on most systems
   
2. **Railway's PORT environment variable**
   - Usually matches your service's default port
   - But always check the logs to confirm

3. **Authentication/Security**
   - Binding to `0.0.0.0` is safe within Railway's private network
   - Still use authentication tokens/passwords as needed

## If Nothing Works

1. Check if the base image has hardcoded localhost bindings
2. Some services require recompilation to change binding addresses
3. Consider using a reverse proxy (nginx, socat) as a last resort

Remember: The goal is to make your service listen on ALL interfaces (0.0.0.0) instead of just localhost. Once it does, Railway's IPv6 private networking will work!