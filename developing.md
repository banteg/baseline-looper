# Developing

## Current Shape

This repo now assumes the live Base YES deployment and no longer tries to preserve Blast compatibility.

- Vyper contract: [Looper.vy](/Users/banteg/dev/0xbaseline/looper/contracts/Looper.vy)
- Ape CLI: [yes.py](/Users/banteg/dev/0xbaseline/looper/scripts/yes.py)
- Ape config: [ape-config.yaml](/Users/banteg/dev/0xbaseline/looper/ape-config.yaml)
- Tests: [test_looper.py](/Users/banteg/dev/0xbaseline/looper/tests/test_looper.py)

## Addresses

- credit facility: `0xc9329Cb681d1338219B9e21E5E99754853436C8D`
- CREDT: `0xa35E4Ac9565Fb006812755C30c369314be3511D9`
- YES / bAsset: `0x1B68244B100A6713ca7F540697b1bE12148a8bf9`
- reserve / WETH: `0x4200000000000000000000000000000000000006`
- Aave V3 Base pool: `0xA238Dd80C259a72e81d7e4664a9801593F98d1c5`
- deployed looper: `0x1B2D303C9e261770F3530e11D64Be996624EAAC1`

## Contract Behavior

`Looper.vy` now:

- derives `reserve`, `bAsset`, `router`, `feeTier`, and `CREDT` from the Base credit facility
- loops by buying YES, calling `borrow(user, collateral, add_days)`, and pulling the borrowed WETH back from the user for the next leg
- unwinds by flash-borrowing reserve from Aave V3 Base, calling `repay(user, amount)`, pulling unlocked YES from the user, swapping it back to WETH, and letting Aave pull repayment

The contract keeps the same public entrypoints:

- `loop(amount, num_loops, add_days)`
- `unwind(min_out)`
- `unwind(min_out, amount)`

## Tests

Fork tests are pinned to Base block `43749913` in [ape-config.yaml](/Users/banteg/dev/0xbaseline/looper/ape-config.yaml). That makes the Base state deterministic and improves Foundry cache reuse.

Run:

```bash
uv run ape test --network base:mainnet-fork:foundry
```

Current result:

- `4` tests passing
- `1` test skipped (`tests/test_weth.py`)

## Operational Notes

- Ape gas estimation was too low on the live Base fork for some market calls, so the CLI and tests use an explicit gas limit for Base transactions
- `ape_foundry` does not currently have a Base hardfork map in its local constants, so the pinned fork block is useful for consistency, but the earlier failure was not caused by a stale foundry hardfork override
