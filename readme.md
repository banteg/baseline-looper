# Baseline Looper

*Loop into [YES]((https://app.baseline.markets/) or unwind a credit account using a flash loan*

## Install

```
pip install -r requirements.txt

ape accounts import anon
```

## Usage

### LOOP da WOOP

Loop into YES with WETH. The contract will buy YES, lock it, borrow WETH, and so on, for as many times as you tell it.

Simply run this and follow the guide.

```
ape run yes loop --network blast:mainnet:geth
```

A residual WETH will be sent back to you. You can buy more YES with it if you want.

If you just want to try it out, install [Foundry](https://book.getfoundry.sh/getting-started/installation) and use the `blast:mainnet-fork:foundry` network.

### UNWIND from ze GRIND

Unwind a credit account and get back into WETH.
The contral will loan WETH enough to repay your principal + interest from [Pac](https://pac.finance/).
Then it will unlock YES, sell it, repay the loan and send you back the remainder.

Run this and follow directions.
```
ape run yes unwind --network blast:mainnet:geth
```

Unwind fees: 0.1% service fee, 0.01% flash loan fee.
