# frontend

(this is outdated and concerns v1)

## contracts and abis

- looper - 0x9525DFc8A9f6A036192c61204E12D5E2267FE8fc - [abi](./contracts/Looper.vy)
- weth - 0x4300000000000000000000000000000000000004 - [abi](./contracts/weth.json)
- yes - 0x1a49351bdB4BE48C0009b661765D01ed58E8C2d8 - [abi](./contracts/BPOOLv1.json)
- credt - 0x158d9270F7931d0eB48Efd72E62c0E9fFfE0E67b - [abi](./contracts/CREDTv1.json)

## general

- if user doesn't have blast network, prompt to add it
- if user has neither eth nor weth on blast, link to bridge
- if user has eth but no weth, suggest to wrap it
    - write `weth.deposit` with value attached

## loop

- user needs weth approval to looper
    - since we pull weth multiple times, we don't know the exact total allowance needed
    - check `weth.allowance(user, looper)`, should be `uint256_max`
    - if not, write `weth.approve(looper, uint256_max)`
- `looper.loop` parameters
    - `amount` [0, `weth.balanceOf(user)`] - the amount of weth to deposit, default to weth balance
    - `num_loops` [1, 69] - how many times to do buy-lock-borrow loop, default to some reasonable value like 10
    - `add_days` [0, 365] - how many days to add to the borrow position. if a user doesn't have an existing credit account (`credit_account.expiry == 0`), default to some reasonable value like 14 or 30, otherwise default to 0. higher value would mean a higher portion would be lost to interest.
- show a simulation of how the user's credit account would be affected by the loop call.
    - before: `credt.getCreditAccount(user)`, returns `(credit, collateral, expiry)`
        - `credit` is the amount of borrowed plus interest in weth
        - `collateral` is the amount of locked yes tokens
        - `expiry` is a unix timestamp in seconds of when the position can be forfeited, 0 if the credit account is empty
    - after: `looper.loop.call(amount, num_loops, add_days)`
        - returns the same struct as `credt.getCreditAccount`
- write `looper.loop(amount, num_loops, add_days)` with the user-input values

## unwind

- user needs yes approval to looper
    - check `yes.allowance(user, looper)` is at least `credit_account.collateral`, otherwise give infinite approval. collateral approval is enoguh too.
    - if not, write `yes.approve(looper, uint256_max)`
- if a user doesn't have a credit account (`expiry == 0`), suggest to go to the loop page
- `looper.unwind` parameters
    - `min_output` [0, inf] - the call will revert if the returned amount is less than the user provided value
- show a simulation of how much weth can be recovered by the unwind call
    - `looper.unwind.call(0)` this will return amount of weth that can be returned
- show a notice about fees: 0.1% service fee, 0.01% flash loan fee
- use a reasonable slippage like 0.5% from the simulated output as `min_output = output * 0.995`
- write `looper.unwind(min_output)`
