#!/usr/bin/env bash

set -e

# Configuration
EXTENSION_ID="vault"
CITIZENS_COUNT=5
REALM_FOLDER="generated_realm"
EXTENSION_DIR="/app/extension-root"

# Run from home directory where realms framework lives
cd /app

echo '[INFO] Cleaning up previous realms installation...'
rm -rf .realms "${REALM_FOLDER}"

echo '[INFO] Packaging vault extension...'
realms extension package --extension-id "${EXTENSION_ID}" --source-dir "${EXTENSION_DIR}"

echo '[INFO] Installing vault extension...'
realms extension install --extension-id "${EXTENSION_ID}" --package-path "/app/${EXTENSION_ID}.zip"

echo '[INFO] Creating test realm with ${CITIZENS_COUNT} citizens...'
realms create --random --citizens "${CITIZENS_COUNT}"

echo '[INFO] Deploying realm to ${REALM_FOLDER}...'
realms deploy --folder "${REALM_FOLDER}"

echo '[INFO] Running vault extension tests...'
realms run --file "${EXTENSION_DIR}/tests/test_vault.py"

echo '[SUCCESS] All tests completed successfully!'
