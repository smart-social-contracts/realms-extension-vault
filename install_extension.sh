#!/usr/bin/env bash

set -e

# Script to uninstall, package, and install a Realms extension
# Usage: ./install_extension.sh <extension-id> <source-dir>

if [ $# -lt 2 ]; then
    echo "Usage: $0 <extension-id> <source-dir>"
    echo "Example: $0 vault .."
    exit 1
fi

EXTENSION_ID="$1"
SOURCE_DIR="$2"
PACKAGE_PATH="${EXTENSION_ID}.zip"

echo '[INFO] Uninstalling all extensions...'
realms extension uninstall --all

echo '[INFO] Packaging vault extension...'
realms extension package --extension-id "${EXTENSION_ID}" --source-dir "${SOURCE_DIR}" --package-path "${PACKAGE_PATH}"

echo '[INFO] Installing vault extension...'
realms extension install --extension-id "${EXTENSION_ID}" --package-path "${PACKAGE_PATH}"

echo '[SUCCESS] Extension installed successfully!'