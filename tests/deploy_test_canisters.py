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
    print("\n[1/8] Creating canisters...")
    run_command(["dfx", "canister", "create", "--all", "--no-wallet"], capture_output=False)


def deploy_ledger(principal: str) -> str:
    """Deploy the ckBTC ledger canister with initial balance."""
    print("\n[2/8] Deploying ckbtc_ledger...")
    
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
    
    print("\n[3/8] Getting ledger canister ID...")
    ledger_id = get_canister_id("ckbtc_ledger")
    print(f"Ledger canister ID: {ledger_id}")
    return ledger_id


def deploy_indexer(ledger_id: str) -> str:
    """Deploy the ckBTC indexer canister."""
    print("\n[4/8] Deploying ckbtc_indexer with ledger reference...")
    
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
    print(f"\n[6/8] Sending {amount:,} ckBTC tokens to realm_backend...")
    
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
        "--output", "json",
        ledger_id, "icrc1_transfer",
        transfer_arg
    ])
    
    # Parse JSON response
    try:
        response_data = json.loads(result.stdout)
        
        if "Ok" in response_data:
            tx_id = int(response_data["Ok"])
            print(f"✅ Transfer successful")
            print(f"   Transaction ID: {tx_id}")
            print(f"   Amount: {amount:,} ckBTC")
            return tx_id
        else:
            error = response_data.get("Err", "Unknown error")
            print(f"❌ Transfer failed: {json.dumps(error, indent=2)}")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse transfer response: {e}")
        print(f"Raw output: {result.stdout}")
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
        "--output", "json",
        ledger_id, "icrc1_balance_of",
        balance_arg
    ])
    
    # Parse JSON response
    try:
        # Response is just a number in JSON format
        balance_str = result.stdout.strip().strip('"')
        # Remove underscores used as thousands separator
        balance = int(balance_str.replace("_", ""))
        return balance
    except (ValueError, json.JSONDecodeError) as e:
        print(f"❌ Failed to parse balance: {e}")
        print(f"Raw output: {result.stdout}")
        sys.exit(1)


def check_indexer_transactions(indexer_id: str, principal: str) -> dict:
    """Query indexer for account transactions and return as JSON."""
    print("\n[8/8] Checking indexer transactions...")
    
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
        "--output", "json",
        indexer_id, "get_account_transactions",
        query_arg
    ])
    
    # Parse the JSON response
    try:
        response_data = json.loads(result.stdout)
        
        # Extract the Ok variant data
        if "Ok" in response_data:
            tx_data = response_data["Ok"]
            
            balance = int(tx_data.get('balance', 0))
            oldest_tx_id = tx_data.get('oldest_tx_id')
            
            print(f"\n✅ Indexer Response:")
            print(f"   Balance: {balance:,} ckBTC")
            print(f"   Transactions: {len(tx_data.get('transactions', []))}")
            print(f"   Oldest TX ID: {oldest_tx_id if oldest_tx_id else 'None'}")
            
            print(f"\n📋 Transactions (JSON):")
            print(json.dumps(tx_data, indent=2))
            
            return tx_data
        else:
            print(f"⚠️  Unexpected response format: {response_data}")
            return {}
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        print(f"Raw output: {result.stdout}")
        return {}


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
    print("\n[5/8] Getting realm_backend canister ID...")
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
    print("\n[7/8] Verifying ledger balance...")
    balance = verify_balance(ledger_id, realm_backend_id)
    print(f"✅ Balance verified: {balance:,} ckBTC")
    
    # Step 8: Check indexer
    tx_data = check_indexer_transactions(indexer_id, realm_backend_id)
    
    print("\n" + "="*60)
    print("🎉 Test Setup Complete!")
    print("="*60)
    print(f"📊 Summary:")
    print(f"  • Tokens sent: 100,000 ckBTC")
    print(f"  • Transaction ID: {tx_id}")
    print(f"  • Current balance: {balance:,} ckBTC")
    print(f"  • Total transactions: {len(tx_data.get('transactions', []))}")
    print(f"  • All data available in JSON format")
    print("="*60)


if __name__ == "__main__":
    main()
