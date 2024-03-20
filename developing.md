# frontend

## contracts and abis

- looper - 0x4494d7Ce28c1AF6F76854258476e099eb80f6D19 - [abi](./contracts/Looper.vy)
- weth - 0x4300000000000000000000000000000000000004 - [abi](./contracts/weth.json)
- yes - 0x20fE91f17ec9080E3caC2d688b4EcB48C5aC3a9C - [abi](./contracts/basset.json)
- baseline - 0x14eB8d9b6e19842B5930030B18c50B0391561f27 - [abi](./contracts/baseline.json)

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
    - before: `baseline.getCreditAccount(user)`, returns `(principal, interest, collateral, expiry, lastFloor)`
        - `principal` is the amount of debt in weth
        - `interest` is the remaining interest to pay back in weth on repay
            - the total debt to repay to unlock all collateral is principal + interest
        - `collateral` is the amount of locked yes tokens
        - `expiry` is a unix timestamp in seconds of when the position can be forfeited, 0 if the credit account is empty
        - `lastFloor` is the floor price in wei when the user last borrowed. when the floor price rises, the user can borrow more.
    - after: `looper.loop.call(amount, num_loops, add_days)`
        - returns the same struct as `baseline.getCreditAccount`
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
