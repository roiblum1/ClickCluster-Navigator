#!/bin/bash
# Script to push OpenShift Cluster Navigator image to various container registries

set -e

VERSION="v1.0.0"
IMAGE_NAME="openshift-cluster-navigator"
TARBALL="docker-images/${IMAGE_NAME}-${VERSION}.tar"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "OpenShift Cluster Navigator - Image Push"
echo -e "==========================================${NC}"
echo ""

# Check if tarball exists
if [ ! -f "$TARBALL" ]; then
    echo -e "${RED}Error: Image tarball not found at $TARBALL${NC}"
    echo "Please build the image first using: podman build -t ${IMAGE_NAME}:${VERSION} ."
    exit 1
fi

echo -e "${GREEN}✓ Found image tarball: $TARBALL${NC}"
echo ""

# Load image
echo -e "${YELLOW}Loading image from tarball...${NC}"
podman load -i "$TARBALL"
echo -e "${GREEN}✓ Image loaded${NC}"
echo ""

# Registry selection
echo "Select target registry:"
echo "1) Quay.io (quay.io)"
echo "2) Docker Hub (docker.io)"
echo "3) OpenShift Internal Registry"
echo "4) Harbor Registry"
echo "5) Custom Registry"
echo "6) All registries"
echo ""
read -p "Enter choice [1-6]: " CHOICE

case $CHOICE in
    1)
        # Quay.io
        echo -e "${BLUE}Pushing to Quay.io${NC}"
        read -p "Enter your Quay.io organization/username: " QUAY_ORG

        echo "Logging in to Quay.io..."
        podman login quay.io

        TARGET_REPO="quay.io/${QUAY_ORG}/${IMAGE_NAME}"

        echo "Tagging image..."
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:${VERSION}
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:latest

        echo "Pushing image..."
        podman push ${TARGET_REPO}:${VERSION}
        podman push ${TARGET_REPO}:latest

        echo -e "${GREEN}✓ Successfully pushed to Quay.io${NC}"
        echo -e "Image available at: ${TARGET_REPO}:${VERSION}"
        ;;

    2)
        # Docker Hub
        echo -e "${BLUE}Pushing to Docker Hub${NC}"
        read -p "Enter your Docker Hub username: " DOCKER_USER

        echo "Logging in to Docker Hub..."
        podman login docker.io

        TARGET_REPO="docker.io/${DOCKER_USER}/${IMAGE_NAME}"

        echo "Tagging image..."
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:${VERSION}
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:latest

        echo "Pushing image..."
        podman push ${TARGET_REPO}:${VERSION}
        podman push ${TARGET_REPO}:latest

        echo -e "${GREEN}✓ Successfully pushed to Docker Hub${NC}"
        echo -e "Image available at: ${TARGET_REPO}:${VERSION}"
        ;;

    3)
        # OpenShift Internal Registry
        echo -e "${BLUE}Pushing to OpenShift Internal Registry${NC}"

        # Check if logged in to OpenShift
        if ! oc whoami &>/dev/null; then
            echo -e "${RED}Error: Not logged in to OpenShift${NC}"
            echo "Please login first: oc login https://api.your-cluster.example.com:6443"
            exit 1
        fi

        # Get registry route
        REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}' 2>/dev/null)

        if [ -z "$REGISTRY" ]; then
            echo -e "${RED}Error: Could not get OpenShift registry route${NC}"
            echo "Make sure the OpenShift registry is exposed"
            exit 1
        fi

        echo "OpenShift Registry: $REGISTRY"
        read -p "Enter OpenShift project/namespace [cluster-navigator]: " OC_PROJECT
        OC_PROJECT=${OC_PROJECT:-cluster-navigator}

        # Create project if it doesn't exist
        oc new-project $OC_PROJECT 2>/dev/null || oc project $OC_PROJECT

        echo "Logging in to OpenShift registry..."
        podman login -u $(oc whoami) -p $(oc whoami -t) $REGISTRY --tls-verify=false

        TARGET_REPO="${REGISTRY}/${OC_PROJECT}/${IMAGE_NAME}"

        echo "Tagging image..."
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:${VERSION}
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:latest

        echo "Pushing image..."
        podman push ${TARGET_REPO}:${VERSION} --tls-verify=false
        podman push ${TARGET_REPO}:latest --tls-verify=false

        echo -e "${GREEN}✓ Successfully pushed to OpenShift Registry${NC}"
        echo -e "Image available at: ${TARGET_REPO}:${VERSION}"
        ;;

    4)
        # Harbor Registry
        echo -e "${BLUE}Pushing to Harbor Registry${NC}"
        read -p "Enter Harbor registry URL (e.g., harbor.example.com): " HARBOR_URL
        read -p "Enter Harbor project name: " HARBOR_PROJECT

        echo "Logging in to Harbor..."
        podman login ${HARBOR_URL}

        TARGET_REPO="${HARBOR_URL}/${HARBOR_PROJECT}/${IMAGE_NAME}"

        echo "Tagging image..."
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:${VERSION}
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:latest

        echo "Pushing image..."
        podman push ${TARGET_REPO}:${VERSION}
        podman push ${TARGET_REPO}:latest

        echo -e "${GREEN}✓ Successfully pushed to Harbor${NC}"
        echo -e "Image available at: ${TARGET_REPO}:${VERSION}"
        ;;

    5)
        # Custom Registry
        echo -e "${BLUE}Pushing to Custom Registry${NC}"
        read -p "Enter registry URL (e.g., registry.example.com): " CUSTOM_REGISTRY
        read -p "Enter repository path (e.g., my-org/my-project): " CUSTOM_PATH

        echo "Logging in to custom registry..."
        podman login ${CUSTOM_REGISTRY}

        TARGET_REPO="${CUSTOM_REGISTRY}/${CUSTOM_PATH}/${IMAGE_NAME}"

        echo "Tagging image..."
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:${VERSION}
        podman tag localhost/${IMAGE_NAME}:${VERSION} ${TARGET_REPO}:latest

        echo "Pushing image..."
        podman push ${TARGET_REPO}:${VERSION}
        podman push ${TARGET_REPO}:latest

        echo -e "${GREEN}✓ Successfully pushed to custom registry${NC}"
        echo -e "Image available at: ${TARGET_REPO}:${VERSION}"
        ;;

    6)
        # All registries
        echo -e "${YELLOW}This will push to multiple registries. You'll need credentials for each.${NC}"
        read -p "Continue? [y/N]: " CONFIRM

        if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 0
        fi

        # Will need to implement each registry push
        echo -e "${YELLOW}Feature not fully implemented yet. Please push to registries individually.${NC}"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}=========================================="
echo "Push Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update Helm values with new image repository"
echo "2. Deploy using: helm install cluster-navigator ./helm/openshift-cluster-navigator"
echo ""
echo "Example Helm command:"
echo "  helm install cluster-navigator ./helm/openshift-cluster-navigator \\"
echo "    --namespace cluster-navigator \\"
echo "    --create-namespace \\"
echo "    --set image.repository=\"${TARGET_REPO}\" \\"
echo "    --set image.tag=\"${VERSION}\""
echo ""
