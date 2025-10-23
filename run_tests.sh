#!/usr/bin/env bash

# Vault Extension Test Runner
# Runs tests inside the realms Docker container

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Docker image to use for realm deployment
REALM_DOCKER_IMAGE="ghcr.io/smart-social-contracts/realms:latest"

# Configuration
EXTENSION_NAME="vault"
CONTAINER_NAME="vault-test" #-$(date +%s)"
EXTENSION_ROOT_DIR="$(pwd)"

# Step 0: Pull the Docker image
log_info "Pulling Docker image..."
docker pull "$REALM_DOCKER_IMAGE"

# Step 1: Clean up any existing containers
log_info "Cleaning up existing containers..."
docker rm -f $(docker ps -aq --filter "name=vault-test") 2>/dev/null || true

# Step 2: Create and start Docker container
log_info "Creating Docker container..."

docker run -d \
    --name "$CONTAINER_NAME" \
    --init \
    -p 8001:8000 \
    "$REALM_DOCKER_IMAGE" \
    sleep infinity

# Copy extension files to container
log_info "Copying extension files to container..."
docker cp "$EXTENSION_ROOT_DIR/." "$CONTAINER_NAME:/app/extension-root"

# Run tests inside container
log_info "Running tests inside container..."
docker exec -i "$CONTAINER_NAME" bash /app/extension-root/test_entrypoint.sh

# Copy logs from container to host for artifacts
log_info "Copying logs from container..."
docker cp "$CONTAINER_NAME:/app/dfx.log" "dfx.log" 2>/dev/null || log_warning "No dfx.log found in container"
docker cp "$CONTAINER_NAME:/app/dfx2.log" "dfx2.log" 2>/dev/null || log_warning "No dfx2.log found in container"
docker cp "$CONTAINER_NAME:/app/realms_cli.log" "realms_cli.log" 2>/dev/null || log_warning "No realms_cli.log found in container"

# Clean up container after tests
log_info "Cleaning up container..."
docker rm -f "$CONTAINER_NAME" || true

log_success "Test run completed!"
