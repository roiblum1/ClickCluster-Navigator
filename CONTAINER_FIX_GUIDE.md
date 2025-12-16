# Container Import Issue Fix Guide

## Problem
Getting `ImportError: cannot import name ClusterValidator from src.utils.validators unknown location` in containerized environment (pod) but works fine on RHEL 9 system.

## Root Causes

### 1. Missing PYTHONPATH (FIXED ✅)
- **Dockerfile** now includes `PYTHONPATH=/app`
- **Helm deployment** now includes `PYTHONPATH=/app` env var

### 2. Potential Additional Issues

Even with PYTHONPATH set, you might still see errors due to:

#### A. Module Structure Issue
The application expects to run from `/app` directory with this structure:
```
/app/
├── src/
│   ├── __init__.py  ← Must exist!
│   ├── main.py
│   ├── utils/
│   │   ├── __init__.py  ← Must exist!
│   │   └── ...
│   └── ...
└── config.json
```

#### B. Missing __init__.py Files
Every Python package directory MUST have an `__init__.py` file (even if empty).

## Fix Steps

### Step 1: Verify __init__.py Files Exist

Run this to check:
```bash
# Check if src/__init__.py exists
ls -la src/__init__.py
```

If missing, create it:
```bash
touch src/__init__.py
```

### Step 2: Rebuild Container with PYTHONPATH

```bash
# Rebuild with the updated Dockerfile
podman build -t openshift-cluster-navigator:v3.1.0 .

# Or if using different tag
podman build -t localhost/openshift-cluster-navigator:v3.1.0 .
```

### Step 3: Test Locally First

```bash
# Run container locally to test
podman run --rm -it \
  -e PYTHONPATH=/app \
  -e LOG_LEVEL=DEBUG \
  -p 8000:8000 \
  openshift-cluster-navigator:v3.1.0
```

### Step 4: Run Diagnostic Script Inside Container

```bash
# Copy diagnostic script into container
podman run --rm -it \
  -v $(pwd)/container_test.sh:/tmp/test.sh:Z \
  openshift-cluster-navigator:v3.1.0 \
  bash /tmp/test.sh
```

Or exec into running pod:
```bash
# Get pod name
kubectl get pods | grep cluster-navigator

# Exec into pod
kubectl exec -it <pod-name> -- bash

# Inside pod, run:
export PYTHONPATH=/app
python -c "from src.utils import ClusterValidator; print('SUCCESS')"
```

### Step 5: Verify Helm Deployment

If using Helm, verify the deployment has PYTHONPATH:

```bash
# Check if PYTHONPATH is in the deployment
kubectl get deployment cluster-navigator -o yaml | grep -A 2 PYTHONPATH
```

Expected output:
```yaml
- name: PYTHONPATH
  value: /app
```

If not there, upgrade the Helm chart:
```bash
helm upgrade cluster-navigator ./helm/openshift-cluster-navigator
```

## Debugging Commands

### Check Pod Logs
```bash
kubectl logs <pod-name>
```

### Check Environment Variables
```bash
kubectl exec <pod-name> -- env | grep PYTHON
```

Expected:
```
PYTHONPATH=/app
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Test Imports Manually
```bash
kubectl exec <pod-name> -- python -c "from src.utils import ClusterValidator; print('OK')"
```

### Check Working Directory
```bash
kubectl exec <pod-name> -- pwd
# Should output: /app

kubectl exec <pod-name> -- ls -la /app/src/
# Should show src/ directory contents
```

## Alternative: Use Python -m Flag

If all else fails, you can run uvicorn with the `-m` flag:

### Update Dockerfile CMD
```dockerfile
# Instead of:
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Use:
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Update Helm Deployment Command
Add to `deployment.yaml`:
```yaml
command: ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Verify the Fix

### 1. Check Container Build
```bash
# Build and inspect
podman build -t test-build .
podman run --rm test-build env | grep PYTHON

# Should show:
# PYTHONPATH=/app
# PYTHONUNBUFFERED=1
# PYTHONDONTWRITEBYTECODE=1
```

### 2. Test Import
```bash
podman run --rm test-build python -c "from src.utils import ClusterValidator; print('✅ Import works!')"
```

### 3. Test Application Start
```bash
podman run --rm -p 8000:8000 test-build
# Should start without import errors
# Check: curl http://localhost:8000/health
```

## Common Mistakes

### ❌ Wrong: Setting PYTHONPATH but working directory is wrong
```dockerfile
WORKDIR /opt/app  # Wrong!
ENV PYTHONPATH=/app  # Doesn't match!
```

### ✅ Correct: PYTHONPATH matches working directory
```dockerfile
WORKDIR /app  # Correct
ENV PYTHONPATH=/app  # Matches!
```

### ❌ Wrong: Missing src/__init__.py
```
/app/
├── src/
│   ├── main.py  # No __init__.py!
│   └── utils/
```

### ✅ Correct: All packages have __init__.py
```
/app/
├── src/
│   ├── __init__.py  # Present!
│   ├── main.py
│   └── utils/
│       └── __init__.py  # Present!
```

## If Still Not Working

### 1. Get Exact Error
```bash
kubectl logs <pod-name> 2>&1 | grep -A 10 "ImportError"
```

### 2. Check Python Path at Runtime
```bash
kubectl exec <pod-name> -- python -c "import sys; print('\n'.join(sys.path))"
```

Should include `/app`.

### 3. Verify File Structure
```bash
kubectl exec <pod-name> -- ls -R /app/src/
```

### 4. Check Import Directly
```bash
kubectl exec <pod-name> -- python -c "
import sys
print('Python path:', sys.path)
print('Working dir:', $(pwd))
try:
    from src.utils import ClusterValidator
    print('SUCCESS')
except Exception as e:
    print('FAILED:', e)
    import traceback
    traceback.print_exc()
"
```

## Files Modified

1. **Dockerfile** - Added `PYTHONPATH=/app` to ENV
2. **helm/openshift-cluster-navigator/templates/deployment.yaml** - Added PYTHONPATH env var
3. **container_test.sh** - Diagnostic script

## Next Steps

1. Rebuild the container image with updated Dockerfile
2. Push to your registry: `localhost/openshift-cluster-navigator:v3.1.0`
3. Upgrade Helm deployment or restart pods
4. Verify with diagnostic commands above

## Contact

If the issue persists after following this guide:
1. Run the diagnostic script and share the output
2. Share the exact error from pod logs
3. Verify all __init__.py files exist in src/ directory
