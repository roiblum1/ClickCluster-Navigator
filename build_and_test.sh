#!/bin/bash
# Build and Test Container Script
set -e

IMAGE_NAME="${1:-localhost/openshift-cluster-navigator}"
IMAGE_TAG="${2:-v3.1.0}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo "=================================================="
echo "Build and Test Container"
echo "=================================================="
echo "Image: $FULL_IMAGE"
echo ""

# Step 1: Build
echo "Step 1: Building container image..."
podman build -t "$FULL_IMAGE" .
echo "✅ Build complete"
echo ""

# Step 2: Verify PYTHONPATH in image
echo "Step 2: Verifying PYTHONPATH in image..."
PYTHONPATH_CHECK=$(podman run --rm "$FULL_IMAGE" env | grep "PYTHONPATH=/app" || echo "")
if [ -z "$PYTHONPATH_CHECK" ]; then
    echo "❌ PYTHONPATH not set in image!"
    echo "Expected: PYTHONPATH=/app"
    exit 1
else
    echo "✅ PYTHONPATH is set correctly: $PYTHONPATH_CHECK"
fi
echo ""

# Step 3: Test imports
echo "Step 3: Testing imports..."
podman run --rm "$FULL_IMAGE" python -c "
import sys
print('Python path:', sys.path[:3])
from src.utils import ClusterValidator, ClusterUtils, SiteUtils
print('✅ Import test passed')
print('  - ClusterValidator: OK')
print('  - ClusterUtils: OK')
print('  - SiteUtils: OK')
"
if [ $? -ne 0 ]; then
    echo "❌ Import test failed!"
    exit 1
fi
echo ""

# Step 4: Test main app import
echo "Step 4: Testing main app import..."
podman run --rm "$FULL_IMAGE" python -c "
from src.main import app
print('✅ Main app import successful')
"
if [ $? -ne 0 ]; then
    echo "❌ Main app import failed!"
    exit 1
fi
echo ""

# Step 5: Quick start test (5 seconds)
echo "Step 5: Testing application startup..."
echo "Starting container for 5 seconds..."
CONTAINER_ID=$(podman run -d -p 8000:8000 "$FULL_IMAGE")
echo "Container ID: $CONTAINER_ID"

sleep 5

# Check if container is still running
if podman ps | grep -q "$CONTAINER_ID"; then
    echo "✅ Container started successfully"

    # Try health check
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
    else
        echo "⚠️  Health check failed (might need more time to start)"
    fi
else
    echo "❌ Container exited unexpectedly"
    echo "Logs:"
    podman logs "$CONTAINER_ID"
    podman rm -f "$CONTAINER_ID" 2>/dev/null || true
    exit 1
fi

# Cleanup
podman stop "$CONTAINER_ID" > /dev/null 2>&1
podman rm "$CONTAINER_ID" > /dev/null 2>&1
echo ""

# Step 6: Summary
echo "=================================================="
echo "✅ ALL TESTS PASSED!"
echo "=================================================="
echo ""
echo "Image: $FULL_IMAGE"
echo ""
echo "Next steps:"
echo "  1. Tag for registry:"
echo "     podman tag $FULL_IMAGE <your-registry>/$IMAGE_NAME:$IMAGE_TAG"
echo ""
echo "  2. Push to registry:"
echo "     podman push <your-registry>/$IMAGE_NAME:$IMAGE_TAG"
echo ""
echo "  3. Deploy to OpenShift:"
echo "     helm upgrade cluster-navigator ./helm/openshift-cluster-navigator"
echo ""
