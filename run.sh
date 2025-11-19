#!/bin/bash

# OpenShift Cluster Navigator - Run Script

set -e

echo "================================"
echo "OpenShift Cluster Navigator"
echo "================================"
echo ""

# Function to setup local environment (venv + dependencies)
setup_local_env() {
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate

    # Install dependencies
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
}

# Function to build podman image
build_podman_image() {
    echo "Building podman image..."
    podman build -t openshift-cluster-navigator .
    echo ""
    echo "Image built successfully!"
    echo "To run: ./run.sh podman"
}

# Function to run with podman
run_podman() {
    # Build the image first
    echo "Building podman image..."
    podman build -t openshift-cluster-navigator .

    # Run the container
    echo "Starting container..."
    podman run -d \
        --name cluster-navigator \
        -p 8000:8000 \
        --health-cmd='python -c "import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")"' \
        --health-interval=30s \
        --health-timeout=10s \
        --health-retries=3 \
        openshift-cluster-navigator

    echo ""
    echo "Container started successfully!"
    echo "Access the UI at: http://localhost:8000"
    echo "API documentation at: http://localhost:8000/api/docs"
    echo ""
    echo "To view logs: podman logs -f cluster-navigator"
    echo "To stop: podman stop cluster-navigator"
    echo "To remove: podman rm cluster-navigator"
}

# Function to run locally
run_local() {
    setup_local_env

    # Run the application
    echo ""
    echo "Starting the application..."
    echo "Access the UI at: http://localhost:8000"
    echo "API documentation at: http://localhost:8000/api/docs"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""

    python -m src.main
}

# Determine which command to execute
case "$1" in
    "build")
        echo "Building local environment..."
        setup_local_env
        echo ""
        echo "Build complete! To run: ./run.sh or ./run.sh run"
        ;;
    "podman-build")
        build_podman_image
        ;;
    "podman")
        run_podman
        ;;
    "run"|"")
        run_local
        ;;
    *)
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  (no args) or 'run'  - Setup venv, install deps, and run locally"
        echo "  build               - Setup venv and install dependencies only (no run)"
        echo "  podman              - Build and run with Podman"
        echo "  podman-build        - Build Podman image only (no run)"
        echo ""
        exit 1
        ;;
esac
