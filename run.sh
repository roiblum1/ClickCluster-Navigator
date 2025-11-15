#!/bin/bash

# OpenShift Cluster Navigator - Run Script

set -e

echo "================================"
echo "OpenShift Cluster Navigator"
echo "================================"
echo ""

# Determine which method to use
if [ "$1" == "podman" ]; then
    echo "Running with Podman..."
    echo ""

    # Build the image
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

else
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

    # Run the application
    echo ""
    echo "Starting the application..."
    echo "Access the UI at: http://localhost:8000"
    echo "API documentation at: http://localhost:8000/api/docs"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""

    python -m src.main
fi
