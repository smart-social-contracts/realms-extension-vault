#!/usr/bin/env bash

# Vault Extension Test Runner
# Clones the realms framework, installs the vault extension, and runs tests

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

# Configuration
REALMS_DIR=".realms"
EXTENSION_ID="vault"
CITIZENS_COUNT=5
REALM_FOLDER="generated_realm"

log_info "Cleaning up previous realms installation..."
rm -rf "${REALMS_DIR}"

if [ ! -d "${REALMS_DIR}" ]; then
    log_info "Cloning realms repository..."
    git clone https://github.com/smart-social-contracts/realms.git "${REALMS_DIR}"
    # Optionally checkout specific version
    # log_warning "Using default branch. Uncomment below to use specific version:"
    # git checkout v1.2.3  # or specific commit
fi

cd "${REALMS_DIR}"

log_info "Installing realms CLI in development mode..."
pipx install -e cli/

log_info "Packaging vault extension..."
realms extension package --extension-id "${EXTENSION_ID}" --source-dir ..

log_info "Installing vault extension..."
realms extension install --extension-id "${EXTENSION_ID}" --package-path "${EXTENSION_ID}.zip"

log_info "Cleaning up previous realm..."
rm -rf "${REALM_FOLDER}"

log_info "Creating test realm with ${CITIZENS_COUNT} citizens..."
realms create --random --citizens "${CITIZENS_COUNT}"

log_info "Deploying realm to ${REALM_FOLDER}..."
realms deploy --folder "${REALM_FOLDER}"

log_info "Running vault extension tests..."
realms run ../tests/test_vault.py

log_success "All tests completed successfully!"

# TODO: Add e2e tests
log_warning "E2E tests not yet implemented"
