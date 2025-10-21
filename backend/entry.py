"""
Vault Extension Entry Point

This extension provides treasury functionality directly embedded in the realm_backend canister.
No separate vault canister is required - all logic runs in the same canister for maximum performance.
"""

import json
import traceback
from typing import Any, Dict

from kybra import Async, ic
from kybra_simple_logging import get_logger

logger = get_logger("extensions.vault")


def convert_principals_to_strings(obj):
    """Recursively convert Principal objects to strings for JSON serialization"""
    from kybra import Principal

    if isinstance(obj, Principal):
        return obj.to_str()
    elif isinstance(obj, dict):
        return {key: convert_principals_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_principals_to_strings(item) for item in obj]
    else:
        return obj


def get_balance(args: str) -> str:
    """
    Get balance for a principal.

    Args:
        args: JSON string with {"principal_id": "xxx"}

    Returns:
        JSON string with {"success": bool, "data": {"Balance": {...}}}
    """
    logger.info(f"vault.get_balance called with args: {args}")

    try:
        from .vault_lib.entities import Balance

        # Parse args
        params = json.loads(args) if isinstance(args, str) else args
        principal_id = params.get("principal_id")

        if not principal_id:
            return json.dumps({"success": False, "error": "principal_id is required"})

        # Get balance from entity
        balance_entity = Balance[principal_id]
        amount = balance_entity.amount if balance_entity else 0

        balance_dict = {
            "principal_id": principal_id,
            "amount": amount,
        }

        logger.info(f"Successfully retrieved balance: {balance_dict}")
        return json.dumps({"success": True, "data": {"Balance": balance_dict}})

    except Exception as e:
        logger.error(f"Error in get_balance: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def get_status(args: str) -> str:
    """
    Get vault status and statistics.

    Args:
        args: JSON string (can be empty dict)

    Returns:
        JSON string with vault stats
    """
    logger.info("vault.get_status called")

    try:
        from .vault_lib.entities import (ApplicationData, Balance, Canisters,
                                         app_data)

        # Gather stats
        app = app_data()
        balances = [
            {"principal_id": b._id, "amount": b.amount} for b in Balance.instances()
        ]
        canisters = [
            {"id": c._id, "principal": c.principal} for c in Canisters.instances()
        ]

        status_dict = {
            "app_data": {
                "admin_principal": app.admin_principal or "",
                "max_results": app.max_results or 20,
                "max_iteration_count": app.max_iteration_count or 5,
                "scan_end_tx_id": app.scan_end_tx_id,
                "scan_start_tx_id": app.scan_start_tx_id,
                "scan_oldest_tx_id": app.scan_oldest_tx_id,
                "sync_status": "Embedded",  # No separate canister sync needed
                "sync_tx_id": 0,
            },
            "balances": balances,
            "canisters": canisters,
        }

        logger.info("Successfully retrieved vault status")
        return json.dumps({"success": True, "data": {"Stats": status_dict}})

    except Exception as e:
        logger.error(f"Error in get_status: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def get_transactions(args: str) -> str:
    """
    Get transaction history for a principal.

    Args:
        args: JSON string with {"principal_id": "xxx"}

    Returns:
        JSON string with transaction list
    """
    logger.info(f"vault.get_transactions called with args: {args}")

    try:
        from .vault_lib.entities import VaultTransaction

        # Parse args
        params = json.loads(args) if isinstance(args, str) else args
        principal_id = params.get("principal_id")

        if not principal_id:
            return json.dumps({"success": False, "error": "principal_id is required"})

        # Get transactions involving this principal
        all_txs = VaultTransaction.instances()
        relevant_txs = [
            tx
            for tx in all_txs
            if tx.principal_from == principal_id or tx.principal_to == principal_id
        ]

        transactions_list = [
            {
                "id": int(tx._id),
                "amount": tx.amount,
                "timestamp": tx.timestamp,
                "principal_from": tx.principal_from,
                "principal_to": tx.principal_to,
                "kind": tx.kind,
            }
            for tx in relevant_txs
        ]

        logger.info(f"Successfully retrieved {len(transactions_list)} transactions")
        return json.dumps(
            {"success": True, "data": {"Transactions": transactions_list}}
        )

    except Exception as e:
        logger.error(f"Error in get_transactions: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def transfer(args: str) -> Async[str]:
    """
    Transfer tokens to a principal (admin only).

    Args:
        args: JSON string with {"to_principal": "xxx", "amount": 100}

    Returns:
        JSON string with transaction ID
    """
    logger.info(f"vault.transfer called with args: {args}")

    try:
        from kybra import Principal

        from .vault_lib.candid_types import Account, ICRCLedger, TransferArg
        from .vault_lib.entities import (Balance, Canisters, VaultTransaction,
                                         app_data)

        # Parse args
        params = json.loads(args) if isinstance(args, str) else args
        to_principal = params.get("to_principal")
        amount = params.get("amount")

        if not to_principal or amount is None:
            return json.dumps(
                {"success": False, "error": "to_principal and amount are required"}
            )

        # Check admin
        app = app_data()
        caller = ic.caller().to_str()
        if app.admin_principal and caller != app.admin_principal:
            return json.dumps({"success": False, "error": "Only admin can transfer"})

        # Get ledger canister
        ledger_canister = Canisters["ckBTC ledger"]
        if not ledger_canister:
            return json.dumps(
                {"success": False, "error": "ckBTC ledger not configured"}
            )

        # Perform ICRC transfer
        ledger = ICRCLedger(Principal.from_str(ledger_canister.principal))
        result = yield ledger.icrc1_transfer(
            TransferArg(
                to=Account(owner=Principal.from_str(to_principal), subaccount=None),
                fee=None,
                memo=None,
                from_subaccount=None,
                created_at_time=None,
                amount=amount,
            )
        )

        # Handle result
        if hasattr(result, "Ok") and result.Ok is not None:
            tx_id = result.Ok

            # Create transaction record
            VaultTransaction(
                _id=tx_id,
                principal_from=ic.id().to_str(),
                principal_to=to_principal,
                amount=amount,
                timestamp=ic.time(),
                kind="transfer",
            )

            # Update balances
            balance = Balance[to_principal] or Balance(_id=to_principal, amount=0)
            balance.amount -= amount

            logger.info(
                f"Successfully transferred {amount} to {to_principal}, tx_id: {tx_id}"
            )
            return json.dumps(
                {
                    "success": True,
                    "data": {"TransactionId": {"transaction_id": int(tx_id)}},
                }
            )
        else:
            error = result.Err if hasattr(result, "Err") else "Unknown error"
            logger.error(f"Transfer failed: {error}")
            return json.dumps({"success": False, "error": str(error)})

    except Exception as e:
        logger.error(f"Error in transfer: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})


def refresh(args: str) -> Async[str]:
    """
    Sync transaction history from ICRC ledger.

    Args:
        args: JSON string (can be empty)

    Returns:
        JSON string with sync summary
    """
    logger.info("vault.refresh called")

    try:
        from .vault_lib.entities import (Balance, Canisters, VaultTransaction,
                                         app_data)
        from .vault_lib.ic_util_calls import get_account_transactions

        app = app_data()
        indexer_canister = Canisters["ckBTC indexer"]

        if not indexer_canister:
            return json.dumps(
                {"success": False, "error": "ckBTC indexer not configured"}
            )

        # Get transactions from indexer
        vault_principal = ic.id().to_str()
        response = yield get_account_transactions(
            canister_id=indexer_canister.principal,
            owner_principal=vault_principal,
            max_results=app.max_results or 20,
            subaccount=None,
            start_tx_id=0,
        )

        # Process transactions
        new_tx_count = 0
        for account_tx in response.transactions:
            tx_id = account_tx["id"]
            tx = account_tx["transaction"]

            # Skip if already exists
            if VaultTransaction[tx_id]:
                continue

            # Process based on type
            if "transfer" in tx and tx["transfer"]:
                transfer_data = tx["transfer"]
                principal_from = transfer_data["from_"]["owner"].to_str()
                principal_to = transfer_data["to"]["owner"].to_str()
                amount = transfer_data["amount"]

                # Create transaction record
                VaultTransaction(
                    _id=tx_id,
                    principal_from=principal_from,
                    principal_to=principal_to,
                    amount=amount,
                    timestamp=tx["timestamp"],
                    kind="transfer",
                )

                # Update balances
                if principal_to == vault_principal:
                    # Deposit: user sent to vault
                    balance = Balance[principal_from] or Balance(
                        _id=principal_from, amount=0
                    )
                    balance.amount += amount
                elif principal_from == vault_principal:
                    # Withdrawal: vault sent to user
                    balance = Balance[principal_to] or Balance(
                        _id=principal_to, amount=0
                    )
                    balance.amount -= amount

                new_tx_count += 1

        logger.info(f"Successfully synced {new_tx_count} new transactions")
        return json.dumps(
            {
                "success": True,
                "data": {
                    "TransactionSummary": {
                        "new_txs_count": new_tx_count,
                        "sync_status": "Synced",
                        "scan_end_tx_id": response.oldest_tx_id or 0,
                    }
                },
            }
        )

    except Exception as e:
        logger.error(f"Error in refresh: {str(e)}\n{traceback.format_exc()}")
        return json.dumps({"success": False, "error": str(e)})
