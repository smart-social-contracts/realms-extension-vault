# Vault Extension for Realms

ckBTC treasury management for Realms. Balance tracking, transaction history, admin transfers, ICRC-1 integration, test mode.

**Requirements:** Python 3.10.7 • dfx • Realms CLI >=0.1.0 • kybra >=0.10.0

```bash
# Quick test
./run_tests.sh

# Install
realms extension install vault --from https://github.com/.../vault-0.1.0.zip
realms deploy --network ic
```

## Usage

```python
from ggg import Treasury
from kybra import ic

treasury = Treasury(_id="main", name="Main Treasury")
treasury.vault_principal_id = ic.id().to_str()
treasury.save()

balance = yield treasury.get_balance()
yield treasury.send(to_principal="...", amount=100)
yield treasury.refresh()

# Test mode: Treasury(_id="test", name="Test", test_mode=True)
```

## API

`get_balance({principal_id})` • `get_status()` • `get_transactions({principal_id, limit?})` • `transfer({to_principal, amount, memo?})` (admin) • `refresh({principal_id})`

## Config

```python
ICRC_LEDGER_CANISTER = "mxzaz-hqaaa-aaaar-qaada-cai"  # ckBTC mainnet
ICRC_INDEX_CANISTER = "n5wcd-faaaa-aaaar-qaaea-cai"
VAULT_ADMINS = ["your-admin-principal"]
```

## Development

```bash
pytest tests/ -v  # Test
realms extension package --extension-id vault --source-dir .  # Package
git tag v0.1.0 && gh release create v0.1.0 vault-0.1.0.zip  # Release
```

## Security

**⚠️ EARLY DEV - NOT PRODUCTION READY** • Funds at risk • Audit required • Protect admin principals • Test on testnet first

## Troubleshooting

**`.realms` won't delete:** `chmod -R +w .realms && rm -rf .realms` • **Extension not found:** `realms extension list` • **History not updating:** `yield treasury.refresh()` • **Permission denied:** Check `VAULT_ADMINS` • **Debug:** `logging.basicConfig(level=logging.DEBUG)`

---

MIT License • [Issues](https://github.com/smart-social-contracts/realms-extension-vault/issues) • [Docs](https://docs.realms.org)

