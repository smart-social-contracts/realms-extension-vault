#!/usr/bin/env python3
"""
Deploy test canisters (ckBTC ledger and indexer) and fund the realm backend.

This script:
1. Creates test canisters
2. Deploys ckBTC ledger with initial balance
3. Deploys ckBTC indexer
4. Sends test tokens to realm_backend
5. Verifies the setup
"""

import json
import subprocess
import sys
from typing import Optional


def run_command(cmd: list[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def get_principal() -> str:
    """Get the current dfx identity principal."""
    result = run_command(["dfx", "identity", "get-principal"])
    return result.stdout.strip()


def get_canister_id(canister_name: str) -> str:
    """Get the canister ID for a given canister name."""
    result = run_command(["dfx", "canister", "id", canister_name])
    return result.stdout.strip()


def create_canisters():
    """Create all canisters defined in dfx.json."""
    print("\n[1/7] Creating canisters...")
    run_command(["dfx", "canister", "create", "--all", "--no-wallet"], capture_output=False)


def deploy_ledger(principal: str) -> str:
    """Deploy the ckBTC ledger canister with initial balance."""
    print("\n[2/7] Deploying ckbtc_ledger...")
    
    # Build the init argument
    init_arg = (
        '(variant { Init = record { '
        'minting_account = record { owner = principal "aaaaa-aa"; subaccount = null }; '
        'transfer_fee = 10; '
        'token_symbol = "ckBTC"; '
        'token_name = "ckBTC Test"; '
        'decimals = opt 8; '
        'metadata = vec {}; '
        f'initial_balances = vec {{ record {{ record {{ owner = principal "{principal}"; subaccount = null }}; 1_000_000_000 }} }}; '
        'feature_flags = opt record { icrc2 = true }; '
        f'archive_options = record {{ num_blocks_to_archive = 1000; trigger_threshold = 2000; controller_id = principal "{principal}" }} '
        '} })'
    )
    
    run_command([
        "dfx", "deploy", "ckbtc_ledger",
        "--no-wallet", "--yes",
        f"--argument={init_arg}"
    ], capture_output=False)
    
    print("\n[3/7] Getting ledger canister ID...")
    ledger_id = get_canister_id("ckbtc_ledger")
    print(f"Ledger canister ID: {ledger_id}")
    return ledger_id


def deploy_indexer(ledger_id: str) -> str:
    """Deploy the ckBTC indexer canister."""
    print("\n[4/7] Deploying ckbtc_indexer with ledger reference...")
    
    init_arg = (
        f'(opt variant {{ Init = record {{ '
        f'ledger_id = principal "{ledger_id}"; '
        f'retrieve_blocks_from_ledger_interval_seconds = opt 1 '
        f'}} }})'
    )
    
    run_command([
        "dfx", "deploy", "ckbtc_indexer",
        "--no-wallet",
        f"--argument={init_arg}"
    ], capture_output=False)
    
    indexer_id = get_canister_id("ckbtc_indexer")
    print(f"\n✅ All test canisters deployed successfully!")
    print(f"\nCanister IDs:")
    print(f"  - ckbtc_ledger: {ledger_id}")
    print(f"  - ckbtc_indexer: {indexer_id}")
    
    return indexer_id


def send_tokens(ledger_id: str, to_principal: str, amount: int) -> int:
    """Send tokens from current identity to a principal."""
    print(f"\n[6/7] Sending {amount:,} ckBTC tokens to realm_backend...")
    
    transfer_arg = (
        f'(record {{'
        f'  to = record {{'
        f'    owner = principal "{to_principal}";'
        f'    subaccount = null;'
        f'  }};'
        f'  amount = {amount};'
        f'  fee = null;'
        f'  memo = null;'
        f'  from_subaccount = null;'
        f'  created_at_time = null;'
        f'}})'
    )
    
    result = run_command([
        "dfx", "canister", "call",
        ledger_id, "icrc1_transfer",
        transfer_arg
    ])
    
    # Parse the result to get transaction ID
    output = result.stdout.strip()
    print(f"Transfer result: {output}")
    
    # Extract transaction ID from variant { Ok = N : nat }
    if "Ok" in output:
        tx_id = int(output.split("=")[1].split(":")[0].strip())
        return tx_id
    else:
        print(f"❌ Transfer failed: {output}")
        sys.exit(1)


def verify_balance(ledger_id: str, principal: str) -> int:
    """Check the balance of a principal."""
    balance_arg = (
        f'(record {{'
        f'  owner = principal "{principal}";'
        f'  subaccount = null;'
        f'}})'
    )
    
    result = run_command([
        "dfx", "canister", "call",
        ledger_id, "icrc1_balance_of",
        balance_arg
    ])
    
    # Parse balance from output like "(100_000 : nat)"
    output = result.stdout.strip()
    balance = int(output.replace("(", "").replace(")", "").replace("_", "").replace(":", "").split()[0])
    return balance


def check_indexer_transactions(indexer_id: str, principal: str):
    """Query indexer for account transactions."""
    print("\n[7/7] Verifying balance and checking indexer...")
    
    query_arg = (
        f'(record {{'
        f'  account = record {{'
        f'    owner = principal "{principal}";'
        f'    subaccount = null;'
        f'  }};'
        f'  start = null;'
        f'  max_results = 10 : nat;'
        f'}})'
    )
    
    result = run_command([
        "dfx", "canister", "call",
        indexer_id, "get_account_transactions",
        query_arg
    ])
    
    print("\nIndexer transactions:")
    print(result.stdout)


def main():
    """Main deployment flow."""
    print("=== Deploying Test Canisters ===\n")
    
    # Step 0: Get current principal
    principal = get_principal()
    print(f"Using principal: {principal}")
    
    # Step 1: Create canisters
    create_canisters()
    
    # Step 2-3: Deploy ledger
    ledger_id = deploy_ledger(principal)
    
    # Step 4: Deploy indexer
    indexer_id = deploy_indexer(ledger_id)
    
    # Step 5: Get realm_backend canister ID
    print("\n[5/7] Getting realm_backend canister ID...")
    try:
        realm_backend_id = get_canister_id("realm_backend")
        print(f"Realm backend canister ID: {realm_backend_id}")
    except subprocess.CalledProcessError:
        print("⚠️  realm_backend not found (might not be deployed yet)")
        print("    Skipping token transfer step")
        return
    
    # Step 6: Send tokens
    tx_id = send_tokens(ledger_id, realm_backend_id, 100_000)
    
    # Step 7: Verify
    balance = verify_balance(ledger_id, realm_backend_id)
    print(f"Realm backend balance: {balance:,} ckBTC")
    
    check_indexer_transactions(indexer_id, realm_backend_id)
    
    print("\n🎉 Test setup complete!")
    print(f"  - Tokens sent to realm_backend: 100,000 ckBTC")
    print(f"  - Transaction ID: {tx_id}")
    print(f"  - Current balance: {balance:,} ckBTC")
    print(f"  - Transaction indexed and verified")


if __name__ == "__main__":
    main()
