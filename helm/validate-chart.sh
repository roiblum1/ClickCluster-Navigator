#!/bin/bash
# Helm Chart Validation Script for OpenShift Cluster Navigator

set -e

CHART_DIR="./openshift-cluster-navigator"
NAMESPACE="cluster-navigator-test"

echo "=========================================="
echo "OpenShift Cluster Navigator - Chart Validation"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "1. Checking prerequisites..."
command -v helm >/dev/null 2>&1 || { echo -e "${RED}✗ helm is required but not installed${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ helm found${NC}"

command -v oc >/dev/null 2>&1 || command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}✗ oc or kubectl is required${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ oc/kubectl found${NC}"
echo ""

# Lint chart
echo "2. Linting Helm chart..."
if helm lint $CHART_DIR; then
    echo -e "${GREEN}✓ Chart linting passed${NC}"
else
    echo -e "${RED}✗ Chart linting failed${NC}"
    exit 1
fi
echo ""

# Template with default values
echo "3. Testing template rendering with default values..."
if helm template test-release $CHART_DIR > /dev/null; then
    echo -e "${GREEN}✓ Template rendering (default values) passed${NC}"
else
    echo -e "${RED}✗ Template rendering failed${NC}"
    exit 1
fi
echo ""

# Template with production values
echo "4. Testing template rendering with production values..."
if helm template test-release $CHART_DIR --values $CHART_DIR/values-production.yaml > /dev/null; then
    echo -e "${GREEN}✓ Template rendering (production values) passed${NC}"
else
    echo -e "${RED}✗ Template rendering (production) failed${NC}"
    exit 1
fi
echo ""

# Template with development values
echo "5. Testing template rendering with development values..."
if helm template test-release $CHART_DIR --values $CHART_DIR/values-development.yaml > /dev/null; then
    echo -e "${GREEN}✓ Template rendering (development values) passed${NC}"
else
    echo -e "${RED}✗ Template rendering (development) failed${NC}"
    exit 1
fi
echo ""

# Dry-run installation
echo "6. Testing dry-run installation..."
if helm install test-release $CHART_DIR --dry-run --debug > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Dry-run installation passed${NC}"
else
    echo -e "${RED}✗ Dry-run installation failed${NC}"
    exit 1
fi
echo ""

# Check for required files
echo "7. Checking for required files..."
required_files=(
    "$CHART_DIR/Chart.yaml"
    "$CHART_DIR/values.yaml"
    "$CHART_DIR/values-production.yaml"
    "$CHART_DIR/values-development.yaml"
    "$CHART_DIR/templates/_helpers.tpl"
    "$CHART_DIR/templates/deployment.yaml"
    "$CHART_DIR/templates/service.yaml"
    "$CHART_DIR/templates/route.yaml"
    "$CHART_DIR/templates/configmap.yaml"
    "$CHART_DIR/templates/secret.yaml"
    "$CHART_DIR/templates/serviceaccount.yaml"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file missing${NC}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    exit 1
fi
echo ""

# Validate YAML syntax
echo "8. Validating YAML syntax..."
for file in $(find $CHART_DIR/templates -name "*.yaml" -o -name "*.tpl"); do
    # Skip files that use Helm templates (will be validated by helm template)
    if grep -q "{{" "$file"; then
        continue
    fi

    if command -v yamllint >/dev/null 2>&1; then
        if yamllint -d relaxed "$file" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $(basename $file)${NC}"
        else
            echo -e "${YELLOW}⚠ $(basename $file) - yamllint warnings${NC}"
        fi
    fi
done
echo ""

# Generate manifests for review
echo "9. Generating manifests for review..."
OUTPUT_DIR="./generated-manifests"
mkdir -p $OUTPUT_DIR

helm template cluster-navigator $CHART_DIR > $OUTPUT_DIR/default-manifests.yaml
helm template cluster-navigator $CHART_DIR --values $CHART_DIR/values-production.yaml > $OUTPUT_DIR/production-manifests.yaml
helm template cluster-navigator $CHART_DIR --values $CHART_DIR/values-development.yaml > $OUTPUT_DIR/development-manifests.yaml

echo -e "${GREEN}✓ Manifests generated in $OUTPUT_DIR/${NC}"
echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "${GREEN}All validation checks passed!${NC}"
echo ""
echo "Next steps:"
echo "1. Review generated manifests in $OUTPUT_DIR/"
echo "2. Test installation: helm install test-release $CHART_DIR --namespace $NAMESPACE --create-namespace"
echo "3. Deploy to production: See helm/DEPLOYMENT_GUIDE.md"
echo ""
