#!/bin/bash
set -e

echo "=== Deploying Test Canisters ==="

# Get current principal for initialization
PRINCIPAL=$(dfx identity get-principal)
echo "Using principal: $PRINCIPAL"

# # Clean up old canister IDs if they exist (handles dfx start --clean scenarios)
# echo ""
# echo "[0/4] Cleaning up stale canister IDs..."
# rm -f .dfx/local/canister_ids.json
# rm -f canister_ids.json

# Step 1: Create canisters
echo ""
echo "[1/4] Creating canisters..."
dfx canister create --all --no-wallet

# Step 2: Deploy the ckBTC ledger
echo ""
echo "[2/4] Deploying ckbtc_ledger..."
dfx deploy ckbtc_ledger --no-wallet --yes --argument="(variant { Init = record { minting_account = record { owner = principal \"aaaaa-aa\"; subaccount = null }; transfer_fee = 10; token_symbol = \"ckBTC\"; token_name = \"ckBTC Test\"; decimals = opt 8; metadata = vec {}; initial_balances = vec { record { record { owner = principal \"$PRINCIPAL\"; subaccount = null }; 1_000_000_000 } }; feature_flags = opt record { icrc2 = true }; archive_options = record { num_blocks_to_archive = 1000; trigger_threshold = 2000; controller_id = principal \"$PRINCIPAL\" } } })"

# Step 3: Get the ledger canister ID
echo ""
echo "[3/4] Getting ledger canister ID..."
LEDGER_ID=$(dfx canister id ckbtc_ledger)
echo "Ledger canister ID: $LEDGER_ID"

# Step 4: Deploy the ckBTC indexer with the ledger ID
echo ""
echo "[4/4] Deploying ckbtc_indexer with ledger reference..."
dfx deploy ckbtc_indexer --no-wallet --argument="(opt variant { Init = record { ledger_id = principal \"$LEDGER_ID\"; retrieve_blocks_from_ledger_interval_seconds = opt 1 } })"

echo ""
echo "✅ All test canisters deployed successfully!"
echo ""
echo "Canister IDs:"
echo "  - ckbtc_ledger: $LEDGER_ID"
echo "  - ckbtc_indexer: $(dfx canister id ckbtc_indexer)"
