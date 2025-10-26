#!/usr/bin/env bash

set -e
set -x

# Configuration
EXTENSION_ID="vault"
CITIZENS_COUNT=5
REALM_FOLDER="generated_realm"
EXTENSION_DIR="extension-root"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Download test artifacts
"${SCRIPT_DIR}/tests/download_test_artifacts.sh"

# Run from home directory where realms framework lives (if in Docker)
if [ -f /.dockerenv ]; then
    cd /app
    # In Docker, create a temp directory with proper structure
    mkdir -p /tmp/extensions/vault
    cp -r extension-root/* /tmp/extensions/vault/
    # Don't copy the .realms directory if it exists (causes conflicts)
    rm -rf /tmp/extensions/vault/.realms
    EXTENSION_SOURCE_DIR="/tmp/extensions"
    TEST_FILE="extension-root/tests/test_vault.py"
else
    # Clone realms repo if not already present
    if [ ! -d ".realms" ]; then
        echo '[INFO] Cloning realms repository...'
        # TODO: using SSH instead of HTTPS for now 
        # git clone https://github.com/smart-social-contracts/realms.git .realms
        git clone git@github.com:smart-social-contracts/realms.git .realms
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
pip install -e cli/ --force

# DO NOT USE THIS APPROACH
# echo '[INFO] Packaging vault extension...'
# realms extension package --extension-id "${EXTENSION_ID}" --source-dir .. --package-path ${EXTENSION_ID}.zip #"${EXTENSION_DIR}" --
# echo '[INFO] Installing vault extension...'
# realms extension install --extension-id "${EXTENSION_ID}" --package-path ${EXTENSION_ID}.zip #"/app/${EXTENSION_ID}.zip"

echo '[INFO] Creating test realm with ${CITIZENS_COUNT} citizens...'
realms create --random #--citizens "${CITIZENS_COUNT}"

echo '[INFO] Removing old vault extension files...'
rm -rf src/realm_backend/extension_packages/vault || true
rm -rf src/realm_frontend/src/lib/extensions/vault || true
rm -rf src/realm_frontend/src/routes/\(sidebar\)/extensions/vault || true

echo '[INFO] Manually copying custom vault extension (backend)...'
cp -r "${EXTENSION_SOURCE_DIR}/vault/backend" src/realm_backend/extension_packages/vault
cp "${EXTENSION_SOURCE_DIR}/vault/manifest.json" src/realm_backend/extension_packages/vault/

echo '[INFO] Manually copying custom vault extension (frontend)...'
# Copy frontend lib components
if [ -d "${EXTENSION_SOURCE_DIR}/vault/frontend/lib/extensions/vault" ]; then
    mkdir -p src/realm_frontend/src/lib/extensions
    cp -r "${EXTENSION_SOURCE_DIR}/vault/frontend/lib/extensions/vault" src/realm_frontend/src/lib/extensions/
fi

# Copy frontend routes
if [ -d "${EXTENSION_SOURCE_DIR}/vault/frontend/routes/(sidebar)/extensions/vault" ]; then
    mkdir -p src/realm_frontend/src/routes/\(sidebar\)/extensions
    cp -r "${EXTENSION_SOURCE_DIR}/vault/frontend/routes/(sidebar)/extensions/vault" src/realm_frontend/src/routes/\(sidebar\)/extensions/
fi

# Copy i18n translations
if [ -d "${EXTENSION_SOURCE_DIR}/vault/frontend/i18n/locales/extensions/vault" ]; then
    mkdir -p src/realm_frontend/i18n/locales/extensions
    cp -r "${EXTENSION_SOURCE_DIR}/vault/frontend/i18n/locales/extensions/vault" src/realm_frontend/i18n/locales/extensions/
fi

echo '[INFO] Creating stub for admin_dashboard extension (if referenced)...'
# Create minimal stub to prevent build errors if admin_dashboard is referenced
if ! [ -f "src/realm_frontend/src/lib/extensions/admin_dashboard/AdminDashboard.svelte" ]; then
    mkdir -p src/realm_frontend/src/lib/extensions/admin_dashboard
    cat > src/realm_frontend/src/lib/extensions/admin_dashboard/AdminDashboard.svelte << 'EOF'
<script>
  // Stub component for admin_dashboard extension
  // This is a placeholder to prevent build errors during testing
</script>

<div>
  <p>Admin Dashboard extension not installed</p>
</div>
EOF
fi

echo '[INFO] Updating extension imports...'
# Make sure vault is in the imports (it should already be there)
if ! grep -q "import extension_packages.vault.entry" src/realm_backend/extension_packages/extension_imports.py; then
    echo "import extension_packages.vault.entry" >> src/realm_backend/extension_packages/extension_imports.py
fi

# Stop previous dfx instances and clean up
echo '[INFO] Stopping previous dfx instances...'
if [ -f /.dockerenv ]; then
    bash /app/extension-root/clean_dfx.sh || true
else
    bash ../clean_dfx.sh || true
fi

# Unify dfx.json files - merge test canisters into .realms/dfx.json
echo '[INFO] Unifying dfx.json configuration...'
# Don't cd into REALM_FOLDER - the dfx.json is in .realms/ not in generated_realm/

# Merge test canisters into unified dfx.json
if [ -f /.dockerenv ]; then
    python3 /app/extension-root/tests/merge_dfx_json.py /app/extension-root/tests/dfx.json dfx.json
else
    # Merge into .realms/dfx.json (we're already in .realms/ directory)
    python3 ../tests/merge_dfx_json.py ../tests/dfx.json dfx.json
fi

echo '[INFO] Deploying realm to ${REALM_FOLDER}...'
realms deploy --folder "${REALM_FOLDER}"

# Deploy test canisters from unified dfx.json
echo '[INFO] Deploying test canisters (ckBTC ledger and indexer)...'
if [ -f /.dockerenv ]; then
    python3 /app/extension-root/tests/deploy_test_canisters.py
else
    python3 ../tests/deploy_test_canisters.py
fi

# Capture the canister IDs AFTER deployment
CKBTC_LEDGER_ID=$(dfx canister id ckbtc_ledger)
CKBTC_INDEXER_ID=$(dfx canister id ckbtc_indexer)
echo "[INFO] ckBTC Ledger ID: ${CKBTC_LEDGER_ID}"
echo "[INFO] ckBTC Indexer ID: ${CKBTC_INDEXER_ID}"


# Configure vault extension with local test canister IDs
echo '[INFO] Configuring vault with local test canister IDs...'
if [ -f /.dockerenv ]; then
    # In Docker environment
    INIT_SCRIPT_SOURCE="/app/extension-root/tests/init_vault_canisters.py"
    INIT_SCRIPT_TEMP="/tmp/init_vault_canisters_configured.py"
else
    # In local environment  
    INIT_SCRIPT_SOURCE="../tests/init_vault_canisters.py"
    INIT_SCRIPT_TEMP="/tmp/init_vault_canisters_configured.py"
fi

# Create a copy of the init script with actual canister IDs injected
sed -e "s/PLACEHOLDER_LEDGER_ID/${CKBTC_LEDGER_ID}/" \
    -e "s/PLACEHOLDER_INDEXER_ID/${CKBTC_INDEXER_ID}/" \
    "${INIT_SCRIPT_SOURCE}" > "${INIT_SCRIPT_TEMP}"

# Run the initialization script with injected canister IDs
realms run --file "${INIT_SCRIPT_TEMP}"

echo '[INFO] Running vault extension tests...'
realms run --file "${TEST_FILE}" --wait

echo '[SUCCESS] All tests completed successfully!'
