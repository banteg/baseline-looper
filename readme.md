# Baseline Looper

Base-only loop and unwind tooling for the Baseline YES market.

The contract now targets the live Base split-credit deployment and uses Aave V3 Base for unwind flash loans. Blast support is intentionally removed on this branch.

## Install

```bash
uv sync
uv run ape accounts import anon
```

## Base Defaults

- credit facility: `0xc9329Cb681d1338219B9e21E5E99754853436C8D`
- CREDT: `0xa35E4Ac9565Fb006812755C30c369314be3511D9`
- YES / bAsset: `0x1B68244B100A6713ca7F540697b1bE12148a8bf9`
- reserve / WETH: `0x4200000000000000000000000000000000000006`
- Aave V3 Base pool: `0xA238Dd80C259a72e81d7e4664a9801593F98d1c5`

## CLI

Deploy a looper:

```bash
uv run ape run yes deploy --network base:mainnet:node
```

Loop into the market:

```bash
LOOPER_ADDRESS=0xYourLooper \
uv run ape run yes loop --network base:mainnet:node
```

Unwind a position:

```bash
LOOPER_ADDRESS=0xYourLooper \
uv run ape run yes unwind --network base:mainnet:node
```

The unwind CLI supports:

- full unwind with divisor `1`
- partial unwind with any divisor such as `3` for a one-third repay

If you are only testing locally, use a fork instead. The fork is pinned in [ape-config.yaml](/Users/banteg/dev/0xbaseline/looper/ape-config.yaml) for deterministic Base state and better Anvil caching:

```bash
uv run ape test --network base:mainnet-fork:foundry
```

## Notes

- the looper pulls WETH back from the user on each loop leg, so users should approve WETH to the looper first
- the unwinder pulls unlocked YES from the user after `repay()`, so users should approve YES to the looper before unwind
- the Ape CLI uses an explicit gas limit on the Base market calls because auto-estimation was too low on the live fork
