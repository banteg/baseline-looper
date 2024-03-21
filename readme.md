# Baseline Looper

*Loop into [YES](https://app.baseline.markets/) or unwind a credit account using a flash loan*

## Install

```
pip install -r requirements.txt

ape accounts import anon
```

## Usage

[Official UI](https://loop-da-woop.vercel.app/) ([repo](https://github.com/pentaclexyz/loop-da-woop))

### LOOP da WOOP

Loop into YES with WETH. The contract will buy YES, lock it, borrow WETH, and so on, for as many times as you tell it.

Simply run this and follow the guide.

```
ape run yes loop --network blast:mainnet:geth
```

A residual WETH will be sent back to you. You can buy more YES with it if you want.

If you just want to try it out, install [Foundry](https://book.getfoundry.sh/getting-started/installation) and use `blast:mainnet-fork:foundry` network.

### UNWIND from ze GRIND

Unwind a credit account and get back into WETH.
The contral will loan WETH enough to repay your principal + interest from [Pac](https://pac.finance/).
Then it will unlock YES, sell it, repay the loan and send you back the remainder.

Run this and follow directions.
```
ape run yes unwind --network blast:mainnet:geth
```

Unwind fees: 0.1% service fee, 0.01% flash loan fee.

## Interact using Foundry

1. Install [Foundry](https://book.getfoundry.sh/getting-started/installation)
2. Import wallet (see other options [here](https://book.getfoundry.sh/reference/cli/cast/wallet/import)) `cast wallet import anon --interactive`
3. Set up the environment
```sh
export looper=0xFfADb825D02f9E6e216cD836e16C33021a87Ec23
export yes=0x20fE91f17ec9080E3caC2d688b4EcB48C5aC3a9C
export weth=0x4300000000000000000000000000000000000004
export baseline=0x14eB8d9b6e19842B5930030B18c50B0391561f27
export ETH_KEYSTORE_ACCOUNT=anon  # the name of your imported wallet
export ETH_FROM=0xYourAddy  # set to your wallet address
export ETH_RPC_URL=https://rpc.blast.io
```

### Loop with Foundry

1. Approve WETH `cast send $weth "approve(address,uint)" $looper $(cast max-uint)`
    - Note that you need to approve more WETH than the amount you are looping.
2. Loop in `cast send $looper "loop(uint,uint,uint)" $(cast --to-wei 10 ether) 10 7`
    - The params are `amount` (in wei), `num_loops` (1-69), `add_days` (use 0 if you already have a credit account)

## Unwind with Foundry

To see your credit account, you can do this:
`cast call $baseline "getCreditAccount(address)(uint,uint,uint,uint,uint) $ETH_FROM`

the returned values are `principal`, `interest`, `collateral`, `expiry`, `lastFloor`.

1. Approve YES `cast send $yes "approve(address,uint)" $looper $(cast max-uint)`
    - You can also approve the exact amount of YES locked up as `collateral`
2. Estimate output `cast call $looper "unwind(uint)(uint)" 0`
3. Unwind the position `cast send $looper "unwind(uint)(uint)" 0`
    - Instead of 0 you can specify the minimum WETH returned. A good value would be `estimate * 0.995` to protect from slippage.

## Deployed contracts

- v0.1.0 = 0x2cb41A98b6b01e50308AEDD754138510e2225933
- v0.2.0 = 0x4494d7Ce28c1AF6F76854258476e099eb80f6D19
    - supports loop with 0 when the floor shifts
    - maximizes efficiency by automatically claiming the boost on repay
    - supports partial repays
- v0.2.1 = 0xFfADb825D02f9E6e216cD836e16C33021a87Ec23
    - return credit account post state from `unwind`
