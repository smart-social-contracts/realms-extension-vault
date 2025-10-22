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
else
    # Clone realms repo if not already present
    if [ ! -d ".realms" ]; then
        echo '[INFO] Cloning realms repository...'
        git clone https://github.com/smart-social-contracts/realms.git .realms
    fi
    cd .realms
fi

echo '[INFO] Cleaning up previous realms installation...'
rm -rf "${REALM_FOLDER}"

echo '[INFO] Packaging vault extension...'
realms extension package --extension-id "${EXTENSION_ID}" --source-dir .. --package-path ${EXTENSION_ID}.zip #"${EXTENSION_DIR}" --

echo '[INFO] Installing vault extension...'
realms extension install --extension-id "${EXTENSION_ID}" --package-path ${EXTENSION_ID}.zip #"/app/${EXTENSION_ID}.zip"

echo '[INFO] Creating test realm with ${CITIZENS_COUNT} citizens...'
realms create --random --citizens "${CITIZENS_COUNT}"

echo '[INFO] Deploying realm to ${REALM_FOLDER}...'
realms deploy --folder "${REALM_FOLDER}"

echo '[INFO] Running vault extension tests...'
realms run --file "${EXTENSION_DIR}/tests/test_vault.py"

echo '[SUCCESS] All tests completed successfully!'
