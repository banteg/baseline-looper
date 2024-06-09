# Baseline Looper

*Loop into [YESv2(real)](https://app.baseline.markets/) or unwind a credit account using a flash loan*

## Install

```
uv pip install -r requirements.txt

ape accounts import anon
```

## Usage

- [First UI](https://loop-da-woop.vercel.app/) ([repo](https://github.com/pentaclexyz/loop-da-woop)) built by pentacle and alice
- [Second UI](https://looper-next.vercel.app/) built by banteg

Read further if you want to use CLI.

### LOOP da WOOP

Loop into YES with WETH. The contract will buy YES, lock it, borrow WETH, and so on, for as many times as you tell it.

Simply run this and follow the guide.

```
ape run yes loop --network blast:mainnet:node
```

A residual WETH will be sent back to you. You can buy more YES with it if you want.

If you just want to try it out, install [Foundry](https://book.getfoundry.sh/getting-started/installation) and use `blast:mainnet-fork:foundry` network.

### UNWIND from ze GRIND

Unwind a credit account and get back into WETH.
The contral will loan WETH enough to repay your principal + interest from [Pac](https://pac.finance/).
Then it will unlock YES, sell it, repay the loan and send you back the remainder.

Run this and follow directions.
```
ape run yes unwind --network blast:mainnet:node
```

Unwind fees: 0.1% service fee, 0.01% flash loan fee.

## Deployed contracts

### YESv2(real)

- v0.3.0 = 0x9525DFc8A9f6A036192c61204E12D5E2267FE8fc
    - support the ree-launched baseline version

### YESv1 (deprecated)

- v0.2.1 = 0xFfADb825D02f9E6e216cD836e16C33021a87Ec23
    - return credit account post state from `unwind`
- v0.2.0 = 0x4494d7Ce28c1AF6F76854258476e099eb80f6D19
    - supports loop with 0 when the floor shifts
    - maximizes efficiency by automatically claiming the boost on repay
    - supports partial repays
- v0.1.0 = 0x2cb41A98b6b01e50308AEDD754138510e2225933
