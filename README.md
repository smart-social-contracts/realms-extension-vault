# Vault Extension for Realms

A secure digital asset and token management extension that provides treasury functionality for Realms.

## Features

- **ckBTC Balance Tracking**: Monitor user deposits and withdrawals
- **Transaction History**: Complete audit trail of all vault operations
- **Admin-Controlled Transfers**: Only realm admins can transfer tokens out
- **ICRC Integration**: Direct integration with ICRC-1 ledger and indexer canisters
- **Test Mode Support**: Mock transactions for development and testing
- **Treasury Integration**: Seamlessly works with Realms Treasury entity

## Architecture

This extension embeds the full vault logic directly in the realm_backend canister, eliminating inter-canister call overhead and providing atomic operations with realm data.

```
realm_backend canister
├── vault extension
│   ├── vault_lib/ (core logic)
│   │   ├── candid_types.py
│   │   ├── constants.py
│   │   ├── entities.py
│   │   ├── ic_util_calls.py
│   │   └── core.py
│   └── entry.py (extension API)
└── ggg/Treasury (integrates with vault)
```

## Installation

### As an Extension Developer (Testing)

```bash
# Clone realms repo at specific version
git clone https://github.com/smart-social-contracts/realms.git
cd realms
git checkout v1.2.3  # or specific commit

# Install realms CLI in dev mode
pip install -e cli/

# Install your extension from local path
realms extension install --source /path/to/realms-extension-vault/

# Deploy locally for testing
dfx start --clean --background
realms deploy --network local

# Run tests
cd /path/to/realms-extension-vault/
pytest tests/
```

### As a Realm Operator (Production)

```bash
# Install from GitHub release
realms extension install vault \
  --from https://github.com/smart-social-contracts/realms-extension-vault/releases/download/v0.1.0/vault-0.1.0.zip

# Or from extension registry (future)
realms extension install vault@0.1.0

# Deploy
realms deploy
```

## Usage

### Initialize Treasury

```python
from ggg import Treasury

# Create treasury linked to your realm
treasury = Treasury(_id="main_treasury", name="Main Treasury")
treasury.vault_principal_id = ic.id().to_str()  # Extension runs in same canister
```

### Check Balance

```python
balance = yield treasury.get_balance()
# Returns: {"principal_id": "xxx", "amount": 1000}
```

### Transfer Tokens

```python
result = yield treasury.send(
    to_principal="recipient-principal-id",
    amount=100
)
# Returns: {"transaction_id": 42}
```

### Sync Transaction History

```python
yield treasury.refresh()
# Updates Treasury with latest transactions from ICRC ledger
```

## Extension API

The extension exposes the following functions:

The extension exposes the following functions:

- `get_balance(args)` - Get balance for a principal
- `get_status(args)` - Get vault status and stats
- `get_transactions(args)` - Get transaction history for a principal
- `transfer(args)` - Transfer tokens to a principal (admin only)
- `refresh(args)` - Sync transaction history from ICRC ledger

## Compatibility

- **Realms Version**: >=0.1.0, <0.2.x
- **Python**: 3.10.7
- **Required Dependencies**:
  - kybra>=0.10.0
  - kybra-simple-db>=1.0.0
  - kybra-simple-logging>=1.0.0

## Development

### Project Structure

```
realms-extension-vault/
├── backend/
│   ├── vault_lib/
│   │   ├── __init__.py
│   │   ├── candid_types.py
│   │   ├── constants.py
│   │   ├── entities.py
│   │   ├── ic_util_calls.py
│   │   └── core.py
│   ├── __init__.py
│   └── entry.py
├── frontend/
│   ├── lib/extensions/vault/
│   └── routes/(sidebar)/extensions/vault/
├── tests/
│   └── test_vault.py
├── manifest.json
├── README.md
└── CHANGELOG.md
```

### Running Tests

```bash
pytest tests/ -v
```

### Packaging for Distribution

```bash
realms extension package .
# Creates: vault-0.1.0.zip
```

### Publishing a Release

```bash
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0

# Create GitHub release with package
gh release create v0.1.0 vault-0.1.0.zip \
  --title "Vault v0.1.0" \
  --notes "Initial release"
```

## Security Considerations

**⚠️ WARNING: This extension is in early development and not production-ready.**

- Funds stored via this extension could be lost
- Only tested on local and staging networks
- Admin controls are critical - protect admin principals
- Test thoroughly before mainnet deployment
- Use test mode for development

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: https://github.com/smart-social-contracts/realms-extension-vault/issues
- **Documentation**: https://github.com/smart-social-contracts/realms-extension-vault
- **Realms Docs**: https://realmsgos.org/docs
