# Container Import Issue - Complete Fix Summary

## Problem Statement
Application works perfectly on RHEL 9 system but fails in containerized pod environment with:
```
ImportError: cannot import name ClusterValidator from src.utils.validators unknown location
```

## Root Cause
**Missing `PYTHONPATH` environment variable in container**

Python couldn't find the `src` module because it wasn't in the Python path. The RHEL 9 system likely had PYTHONPATH set or ran from the correct directory, but the container did not.

## Fixes Applied

### 1. Dockerfile (✅ FIXED)
**File:** `Dockerfile`
**Change:** Added `PYTHONPATH=/app` to environment variables

```dockerfile
# Before (BROKEN)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ...

# After (FIXED)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \            # ← ADDED THIS
    APP_TITLE="OpenShift Cluster Navigator" \
    ...
```

### 2. Helm Deployment (✅ FIXED)
**File:** `helm/openshift-cluster-navigator/templates/deployment.yaml`
**Change:** Added `PYTHONPATH` environment variable

```yaml
# Before (BROKEN)
env:
- name: PYTHONUNBUFFERED
  value: "1"
ports:

# After (FIXED)
env:
- name: PYTHONUNBUFFERED
  value: "1"
- name: PYTHONPATH        # ← ADDED THIS
  value: "/app"           # ← ADDED THIS
ports:
```

## Why This Happens

### Working in RHEL 9
When you run on RHEL 9 directly:
```bash
cd /path/to/ClickCluster-Navigator
python -m uvicorn src.main:app
```
- Current directory is in Python path
- Python can find `src/` module
- ✅ Works

### Broken in Container (Before Fix)
```dockerfile
WORKDIR /app
CMD ["uvicorn", "src.main:app", ...]
```
- `uvicorn` executable doesn't add `/app` to Python path automatically
- Python can't find `src/` module
- ❌ Fails with ImportError

### Fixed in Container (After Fix)
```dockerfile
WORKDIR /app
ENV PYTHONPATH=/app  # ← Python now knows to look in /app
CMD ["uvicorn", "src.main:app", ...]
```
- Python path includes `/app`
- Python can find `src/` module
- ✅ Works

## How to Apply the Fix

### Option 1: Rebuild Container (Recommended)

```bash
# 1. Build with updated Dockerfile
podman build -t localhost/openshift-cluster-navigator:v3.1.0 .

# 2. Test locally
podman run -d -p 8000:8000 localhost/openshift-cluster-navigator:v3.1.0

# 3. Verify it works
curl http://localhost:8000/health

# 4. Tag for your registry
podman tag localhost/openshift-cluster-navigator:v3.1.0 <your-registry>/openshift-cluster-navigator:v3.1.0

# 5. Push to registry
podman push <your-registry>/openshift-cluster-navigator:v3.1.0
```

### Option 2: Quick Test (Temporary Fix)

If you want to test before rebuilding, add PYTHONPATH to your running pod:

```bash
# Edit deployment
kubectl edit deployment cluster-navigator

# Add this under containers[].env:
- name: PYTHONPATH
  value: "/app"

# Save and exit - pod will restart automatically
```

### Option 3: Helm Upgrade

If using Helm:

```bash
# Upgrade with updated Helm chart
helm upgrade cluster-navigator ./helm/openshift-cluster-navigator

# Helm will recreate pods with new env vars
```

## Verification Steps

### 1. Check Environment Variable is Set

```bash
# Get pod name
POD_NAME=$(kubectl get pods -l app=cluster-navigator -o jsonpath='{.items[0].metadata.name}')

# Check PYTHONPATH
kubectl exec $POD_NAME -- env | grep PYTHONPATH
```

Expected output:
```
PYTHONPATH=/app
```

### 2. Test Import Manually

```bash
kubectl exec $POD_NAME -- python -c "from src.utils import ClusterValidator; print('✅ SUCCESS')"
```

Should print: `✅ SUCCESS`

### 3. Check Application Logs

```bash
kubectl logs $POD_NAME
```

Should see application starting without import errors.

### 4. Health Check

```bash
kubectl exec $POD_NAME -- curl -s http://localhost:8000/health
```

Should return:
```json
{"status":"healthy","service":"openshift-cluster-navigator"}
```

## Automated Testing

We've created scripts to help you verify the fix:

### 1. Build and Test Script
```bash
./build_and_test.sh
```

This script:
- Builds the container
- Verifies PYTHONPATH is set
- Tests imports
- Tests application startup
- Confirms everything works

### 2. Container Diagnostic Script
```bash
# Copy script into running pod
kubectl cp container_test.sh $POD_NAME:/tmp/test.sh

# Run diagnostic
kubectl exec $POD_NAME -- bash /tmp/test.sh
```

This will show you exactly what's wrong (if anything).

## Files Modified

| File | Change | Status |
|------|--------|--------|
| `Dockerfile` | Added `PYTHONPATH=/app` | ✅ FIXED |
| `helm/.../deployment.yaml` | Added PYTHONPATH env var | ✅ FIXED |
| `build_and_test.sh` | Created build/test automation | ✅ NEW |
| `container_test.sh` | Created diagnostic script | ✅ NEW |
| `CONTAINER_FIX_GUIDE.md` | Created troubleshooting guide | ✅ NEW |

## Why It Works on RHEL 9

When you run directly on RHEL 9, one of these is likely true:

1. **You're in the project directory:**
   ```bash
   cd /path/to/ClickCluster-Navigator
   python -m uvicorn src.main:app
   ```
   Python automatically adds current directory to path.

2. **PYTHONPATH is set in your shell:**
   ```bash
   export PYTHONPATH=/path/to/ClickCluster-Navigator
   ```

3. **You installed it as a package:**
   ```bash
   pip install -e .
   ```
   The package is in site-packages.

In containers, none of these apply - you must explicitly set PYTHONPATH.

## Troubleshooting

### Still Getting Import Errors?

1. **Verify PYTHONPATH is actually set:**
   ```bash
   kubectl exec $POD_NAME -- python -c "import os; print(os.environ.get('PYTHONPATH', 'NOT SET'))"
   ```

2. **Check working directory:**
   ```bash
   kubectl exec $POD_NAME -- pwd
   ```
   Should be `/app`

3. **Verify src/ exists:**
   ```bash
   kubectl exec $POD_NAME -- ls -la /app/src/
   ```

4. **Test import step by step:**
   ```bash
   kubectl exec $POD_NAME -- python -c "import sys; print(sys.path)"
   kubectl exec $POD_NAME -- python -c "import src"
   kubectl exec $POD_NAME -- python -c "from src import utils"
   kubectl exec $POD_NAME -- python -c "from src.utils import ClusterValidator"
   ```

### Different Error After Fix?

If you're seeing a different error now, it means the PYTHONPATH fix worked but there's another issue. Share the new error message for specific help.

## Summary

**Problem:** Import errors in container (but works on RHEL 9)
**Cause:** Missing PYTHONPATH environment variable
**Solution:** Added `PYTHONPATH=/app` to Dockerfile and Helm deployment
**Status:** ✅ FIXED

**Next Steps:**
1. Rebuild container with `podman build`
2. Test locally with `podman run`
3. Push to registry
4. Deploy to OpenShift/Kubernetes
5. Verify with health check

---

**Need Help?**
- Run `./build_and_test.sh` to verify your build
- Run `./container_test.sh` inside pod to diagnose
- Check `CONTAINER_FIX_GUIDE.md` for detailed troubleshooting
