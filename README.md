# Akash Deployment Top-up Action

Automatically monitor and top up Akash Network deployments when their balances fall below specified thresholds.

## Features

- Monitors active deployment balances
- Automatically tops up deployments when funds are low
- Configurable balance thresholds and top-up amounts
- Supports multiple deployments
- Detailed GitHub Actions output and logging

## Usage

Add this action to your workflow:

```yaml
- uses: lumeweb/akash-topup-action@v0.1.0
  with:
    mnemonic: ${{ secrets.AKASH_MNEMONIC }}
    cert-content: ${{ secrets.AKASH_CERT }}
    cert-id: ${{ secrets.AKASH_CERT_ID }}
    depositor-account: ${{ secrets.AKASH_DEPOSITOR }}
    fee-account: ${{ secrets.AKASH_FEE_ACCOUNT }}
    min-balance-threshold: "1.0"  # AKT
    top-up-amount: "0.5"         # AKT
    block-buffer: "1000"         # blocks
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `mnemonic` | Recovery phrase for the wallet | Yes | - |
| `cert-content` | Certificate content for Akash authentication | Yes | - |
| `cert-id` | Certificate ID for Akash authentication | Yes | - |
| `depositor-account` | Akash depositor account address | Yes | - |
| `fee-account` | Akash fee account address | Yes | - |
| `min-balance-threshold` | Balance threshold to trigger top-up (in AKT) | Yes | - |
| `top-up-amount` | Amount to add (minimum 0.5 AKT) | Yes | - |
| `block-buffer` | Safety margin in blocks before estimated closure | No | 1000 |

## Outputs

| Output | Description |
|--------|-------------|
| `summary` | JSON summary of all actions taken |
| `deployments_checked` | Number of deployments checked |
| `deployments_funded` | Number of deployments funded |
| `total_funded_akt` | Total amount funded in AKT |

## Example Workflow

```yaml
name: Monitor Akash Deployments

on:
  schedule:
    - cron: '0 * * * *'  # Run every hour
  workflow_dispatch:  # Allow manual triggers

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: lumeweb/akash-topup-action@v0.1.6
        with:
          mnemonic: ${{ secrets.AKASH_MNEMONIC }}
          cert-content: ${{ secrets.AKASH_CERT }}
          cert-id: ${{ secrets.AKASH_CERT_ID }}
          depositor-account: ${{ secrets.AKASH_DEPOSITOR }}
          fee-account: ${{ secrets.AKASH_FEE_ACCOUNT }}
          min-balance-threshold: "1.0"
          top-up-amount: "0.5"
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/lumeweb/akash-topup-action
cd akash-topup-action

# Install dependencies
pip install -r requirements.txt
```

### Testing

```bash
# Run tests with coverage
pytest --cov=scripts tests/
```

### Local Usage

The action can also be used as a standalone CLI tool:

```bash
python -m scripts.cli --min-balance 1.0 --top-up 0.5 --block-buffer 1000
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
