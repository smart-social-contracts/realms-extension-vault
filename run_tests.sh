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

# Run tests inside container and collect logs
log_info "Running tests inside container..."
set +e  # Don't exit on test failure - we want to collect logs either way
docker exec -i "$CONTAINER_NAME" bash /app/extension-root/test_entrypoint.sh
EXIT_CODE=$?
set -e

# Collect all logs from inside the container
log_info "Collecting logs from container..."
docker exec "$CONTAINER_NAME" bash -c "
    mkdir -p /app/test-logs && \
    cp -f /app/dfx.log /app/test-logs/ 2>/dev/null || true && \
    cp -f /app/dfx2.log /app/test-logs/ 2>/dev/null || true && \
    cp -f /app/realms_cli.log /app/test-logs/ 2>/dev/null || true && \
    cp -f /tmp/deploy.log /app/test-logs/ 2>/dev/null || true && \
    cp -f /app/generated_realm/.dfx/network/local/dfx.log /app/test-logs/realm_dfx.log 2>/dev/null || true && \
    ls -lah /app/test-logs/ || true
"

# Copy the entire test-logs directory from container to host
log_info "Copying test logs to host..."
docker cp "$CONTAINER_NAME:/app/test-logs" "./test-logs" 2>/dev/null || log_warning "No test-logs directory found in container"

# Clean up container after tests
log_info "Cleaning up container..."
docker rm -f "$CONTAINER_NAME" || true

if [ $EXIT_CODE -eq 0 ]; then
    log_success "Test run completed successfully!"
else
    echo -e "${YELLOW}[WARNING]${NC} Tests failed with exit code $EXIT_CODE"
    echo -e "${BLUE}[INFO]${NC} Check test-logs/ directory for detailed logs"
fi

exit $EXIT_CODE
