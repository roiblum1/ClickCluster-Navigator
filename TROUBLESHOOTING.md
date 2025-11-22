# Troubleshooting Guide

## VLAN Manager Connection Issues

### Error: "Failed to fetch from /api/segments: All connection attempts failed"

**Problem**: The application cannot connect to the VLAN Manager API.

**Common Causes**:

1. **Incorrect URL in config.json**
   - ❌ Wrong: `"url": "http://0.0.0.0:9000"`
   - ✅ Correct: `"url": "http://127.0.0.1:9000"` (for local)
   - ✅ Correct: `"url": "http://vlan-manager:9000"` (for Docker/K8s)

2. **VLAN Manager not running**
   ```bash
   # Check if VLAN Manager is running
   curl http://127.0.0.1:9000/api/segments

   # Start VLAN Manager if needed
   cd /path/to/vlan-manager
   python main.py
   ```

3. **Firewall blocking connection**
   ```bash
   # Check if port is open
   netstat -tuln | grep 9000

   # Test connectivity
   telnet 127.0.0.1 9000
   ```

4. **Different host/container network**
   - If running in Docker, use the service name or host.docker.internal
   - If running in Kubernetes, use the service DNS name

**Solution**:

Edit `config.json`:
```json
{
  "vlan_manager": {
    "url": "http://127.0.0.1:9000",
    "sync_interval_seconds": 300
  }
}
```

Then restart the application.

### Error: "No cached data available"

**Problem**: First time running, no cache exists yet.

**Solution**:
- This is normal on first run
- The application will create cache after successful sync
- Ensure VLAN Manager is accessible first

### VLAN Manager Returns Empty Data

**Problem**: Sync succeeds but no clusters appear.

**Debugging**:
```bash
# Check what VLAN Manager returns
curl http://127.0.0.1:9000/api/segments

# Should return segments with cluster_name not null and released=false
```

**Check**:
1. Are there allocated segments with `cluster_name` set?
2. Are segments marked as `released: false`?
3. Does the response include `site` field?

Example of valid segment:
```json
{
  "_id": "1",
  "site": "Site1",
  "vlan_id": 32,
  "epg_name": "EPG_ROI",
  "segment": "192.168.1.0/24",
  "vrf": "Network1",
  "cluster_name": "ocp4-roi",
  "allocated_at": "2025-11-21T19:38:03.429424+00:00",
  "released": false
}
```

## Application Won't Start

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in config.json
{
  "application": {
    "port": 8001
  }
}
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'httpx'`

**Solution**:
```bash
# Install dependencies
pip install -r requirements.txt

# Or in virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## Docker/Podman Issues

### Image Won't Build

**Error**: Build failures

**Solution**:
```bash
# Clear build cache
podman system prune -a

# Rebuild
podman build -t openshift-cluster-navigator:v1.0.0 .
```

### Container Exits Immediately

**Check logs**:
```bash
podman logs <container-id>
```

**Common issues**:
- Wrong environment variables
- VLAN Manager not accessible from container
- Port conflicts

**Solution**:
```bash
# Run with proper environment
podman run -d \
  --name cluster-navigator \
  -p 8000:8000 \
  -e APP_TITLE="Cluster Navigator" \
  -e ADMIN_USERNAME="admin" \
  -e ADMIN_PASSWORD="SecurePass123" \
  --add-host=host.docker.internal:host-gateway \
  docker.io/roi12345/openshift-cluster-navigator:v1.0.0

# Update config to use host.docker.internal for VLAN Manager
# Or use --network=host for simple local testing
```

### Can't Access from Browser

**Check**:
1. Container is running: `podman ps`
2. Port mapping is correct: `-p 8000:8000`
3. Try: `http://localhost:8000`
4. Check firewall: `sudo ufw allow 8000`

## Kubernetes/OpenShift Issues

### Pods Crashing

**Check logs**:
```bash
oc logs -f deployment/cluster-navigator
```

**Common issues**:
1. **Image pull errors**: Check imagePullSecrets
2. **VLAN Manager unreachable**: Update service URL in ConfigMap
3. **Resource limits**: Increase memory/CPU limits

**Solution**:
```bash
# Update VLAN Manager URL
helm upgrade cluster-navigator ./helm/openshift-cluster-navigator \
  --reuse-values \
  --set app.vlanManagerUrl="http://vlan-manager.vlan-system.svc:9000"
```

### Can't Access via Route

**Check**:
```bash
# Get route
oc get route cluster-navigator

# Test from within cluster
oc run test-curl --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://cluster-navigator:8000/health

# Check route TLS
oc describe route cluster-navigator
```

## Authentication Issues

### Can't Login

**Check**:
1. Correct username/password in config or environment
2. Check secret if using Kubernetes:
   ```bash
   oc get secret cluster-navigator-credentials -o yaml
   # Decode password
   echo "BASE64_PASSWORD" | base64 -d
   ```

**Reset password**:
```bash
# Update environment variable
export ADMIN_PASSWORD="NewPassword123"

# Or update config.json
{
  "auth": {
    "admin_password": "NewPassword123"
  }
}

# Restart application
```

## Performance Issues

### Slow Response Times

**Check**:
1. VLAN Manager response time: `curl -w "@curl-format.txt" http://127.0.0.1:9000/api/segments`
2. Cache file size: `ls -lh data/vlan_cache.json`
3. Number of clusters: Check if filtering is working

**Optimize**:
```bash
# Reduce sync interval if too frequent
{
  "vlan_manager": {
    "sync_interval_seconds": 600
  }
}
```

### High Memory Usage

**Monitor**:
```bash
# Docker/Podman
podman stats cluster-navigator

# Kubernetes
oc adm top pod -l app.kubernetes.io/name=openshift-cluster-navigator
```

**Solution**: Increase resource limits in Helm values or reduce replica count

## Data Issues

### Clusters Not Showing Up

**Debug**:
```bash
# Check cache
cat data/vlan_cache.json | jq '.data.clusters'

# Trigger manual sync
curl -X POST http://localhost:8000/api/vlan-sync/sync \
  -u admin:Password1

# Check logs
tail -f logs/app.log
```

### Duplicate Clusters

**Fixed in v1.0.0**: Clusters can now have same name in different sites

**Verify**:
```bash
# Check cache for composite keys
cat data/vlan_cache.json | jq '.data.clusters[] | {name: .clusterName, site: .site}'
```

### Clusters Not Splitting (Shared Segments)

**Fixed in v1.0.0**: Comma-separated cluster names are split

**Example**: `"cluster_name": "ocp4-roi,ocp4-roi2"` creates 2 separate clusters

**Verify**: Check the UI or API - should see individual cluster cards

## Git LFS Issues

### Can't Push to GitHub

**Error**: `File exceeds GitHub's file size limit of 100.00 MB`

**Solution**: Already fixed with Git LFS migration

**Verify**:
```bash
git lfs ls-files
# Should show: docker-images/openshift-cluster-navigator-v1.0.0.tar
```

**If still having issues**:
```bash
# Re-migrate
git lfs migrate import --include="docker-images/*.tar" --everything

# Force push (WARNING: rewrites history)
git push --force-with-lease origin main
```

## Getting Help

### Enable Debug Logging

Edit `src/main.py` or set environment:
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn src.main:app --reload
```

### Check Health

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"openshift-cluster-navigator"}
```

### Collect Information for Bug Report

```bash
# Version info
podman --version
python --version
helm version

# Application logs
podman logs cluster-navigator > logs.txt

# Configuration (remove sensitive data!)
cat config.json

# Test connectivity
curl -v http://127.0.0.1:9000/api/segments > vlan-manager-test.txt
curl -v http://localhost:8000/health > app-health.txt
```

## Common Quick Fixes

```bash
# Fix 1: Restart everything
podman restart cluster-navigator

# Fix 2: Clear cache and resync
rm data/vlan_cache.json
curl -X POST http://localhost:8000/api/vlan-sync/sync -u admin:Password1

# Fix 3: Rebuild and restart
podman build -t openshift-cluster-navigator:v1.0.0 .
podman stop cluster-navigator && podman rm cluster-navigator
podman run -d --name cluster-navigator -p 8000:8000 \
  openshift-cluster-navigator:v1.0.0

# Fix 4: Check VLAN Manager
curl http://127.0.0.1:9000/api/segments | jq '.'
```
