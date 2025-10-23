#!/usr/bin/env bash

set -e
set -x

# Configuration
EXTENSION_ID="vault"
CITIZENS_COUNT=5
REALM_FOLDER="generated_realm"
EXTENSION_DIR="extension-root"

# Run from home directory where realms framework lives (if in Docker)
if [ -f /.dockerenv ]; then
    cd /app
    # In Docker, create a temp directory with proper structure
    mkdir -p /tmp/extensions/vault
    cp -r extension-root/* /tmp/extensions/vault/
    EXTENSION_SOURCE_DIR="/tmp/extensions"
    TEST_FILE="extension-root/tests/test_vault.py"
else
    # Clone realms repo if not already present
    if [ ! -d ".realms" ]; then
        echo '[INFO] Cloning realms repository...'
        git clone https://github.com/smart-social-contracts/realms.git .realms
    fi
    cd .realms
    # Create a temp directory with proper structure for local dev
    mkdir -p /tmp/extensions/vault
    cp -r ../* /tmp/extensions/vault/ 2>/dev/null || true
    rm -rf /tmp/extensions/vault/.realms  # Don't copy the .realms directory itself
    EXTENSION_SOURCE_DIR="/tmp/extensions"
    TEST_FILE="../tests/test_vault.py"
fi

echo '[INFO] Cleaning up previous realms installation...'
rm -rf "${REALM_FOLDER}"

# Install realms cli
echo '[INFO] Installing realms cli...'
pipx install -e cli/ --force

# DO NOT USE THIS APPROACH
# echo '[INFO] Packaging vault extension...'
# realms extension package --extension-id "${EXTENSION_ID}" --source-dir .. --package-path ${EXTENSION_ID}.zip #"${EXTENSION_DIR}" --
# echo '[INFO] Installing vault extension...'
# realms extension install --extension-id "${EXTENSION_ID}" --package-path ${EXTENSION_ID}.zip #"/app/${EXTENSION_ID}.zip"

echo '[INFO] Installing vault extension from source...'
realms extension install-from-source --source-dir "${EXTENSION_SOURCE_DIR}"

echo '[INFO] Creating test realm with ${CITIZENS_COUNT} citizens...'
realms create --random #--citizens "${CITIZENS_COUNT}"

echo '[INFO] Deploying realm to ${REALM_FOLDER}...'
realms deploy --folder "${REALM_FOLDER}"

echo '[INFO] Running vault extension tests...'
realms run --file "${TEST_FILE}"

echo '[SUCCESS] All tests completed successfully!'
