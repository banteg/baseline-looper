# pragma version ~=0.4.3
# @author banteg
# @title Baseline Base Looper
# @notice Loop into a Baseline Base market or unwind your position without needing upfront WETH.
# @custom:contract-version 0.4.0

interface ERC20:
    def balanceOf(account: address) -> uint256: view
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, recipient: address, amount: uint256) -> bool: nonpayable
    def approve(spender: address, amount: uint256) -> bool: nonpayable

struct Borrow:
    principal: uint256
    interest: uint256
    expiry: uint256

struct ExactInputSingleParams:
    token_in: address
    token_out: address
    fee: uint24
    recipient: address
    deadline: uint256
    amount_in: uint256
    amount_out_minimum: uint256
    sqrt_price_limit_x96: uint160

struct CreditAccount:
    credit: uint256
    collateral: uint256
    expiry: uint256

event Unwound:
    user: indexed(address)
    credit_repaid: uint256
    collateral_unlocked: uint256
    reserve_recovered: uint256
    reserve_spent_on_flash: uint256
    remaining_credit: uint256
    remaining_collateral: uint256

interface AavePool:
    def flashLoanSimple(receiverAddress: address, asset: address, amount: uint256, params: Bytes[128], referralCode: uint16): nonpayable

interface CreditFacility:
    def reserve() -> address: view
    def bAsset() -> address: view
    def router() -> address: view
    def feeTier() -> uint24: view
    def CREDT() -> address: view
    def borrow(user: address, amount: uint256, add_days: uint256) -> Borrow: nonpayable
    def repay(user: address, amount: uint256) -> uint256: nonpayable

interface Credt:
    def getCreditAccount(user: address) -> CreditAccount: view

interface SwapRouter:
    def exactInputSingle(params: ExactInputSingleParams) -> uint256: payable


aave_pool: immutable(AavePool)
router: immutable(SwapRouter)
reserve: immutable(ERC20)
basset: immutable(ERC20)
credit_facility: immutable(CreditFacility)
credt: immutable(Credt)


@deploy
def __init__(credit_facility_: address, aave_pool_: address):
    credit_facility = CreditFacility(credit_facility_)
    aave_pool = AavePool(aave_pool_)
    router = SwapRouter(staticcall credit_facility.router())
    reserve = ERC20(staticcall credit_facility.reserve())
    basset = ERC20(staticcall credit_facility.bAsset())
    credt = Credt(staticcall credit_facility.CREDT())

    extcall basset.approve(credit_facility.address, max_value(uint256))
    extcall reserve.approve(credit_facility.address, max_value(uint256))
    extcall reserve.approve(aave_pool.address, max_value(uint256))
    extcall reserve.approve(router.address, max_value(uint256))
    extcall basset.approve(router.address, max_value(uint256))


@external
def loop(amount: uint256, num_loops: uint256, add_days: uint256) -> CreditAccount:
    """
    @notice Loop with WETH. Buys YES, locks it, borrows WETH, and repeats.
    @dev Requires reserve approval because the looper pulls each borrowed leg back in.
    @param amount How much reserve to use for looping.
    @param num_loops [1-69] How many times to do the buy-lock-borrow loop.
    @param add_days How many days to add to the credit account expiry.
    @return The resulting state of the credit account.
    """
    assert num_loops > 0  # dev: min 1 loop
    assert num_loops < 70  # dev: max 69 loops
    days: uint256 = add_days
    borrow: Borrow = empty(Borrow)

    if amount > 0:
        extcall reserve.transferFrom(msg.sender, self, amount)
        self.buy_basset()

    for i: uint256 in range(70):
        if i == num_loops:
            break
        if i == 1:
            days = 0
        borrow = extcall credit_facility.borrow(msg.sender, staticcall basset.balanceOf(self), days)
        if i < num_loops - 1:
            extcall reserve.transferFrom(msg.sender, self, borrow.principal)
            self.buy_basset()

    return staticcall credt.getCreditAccount(msg.sender)


@external
def unwind(min_out: uint256, amount: uint256 = max_value(uint256)) -> (uint256, CreditAccount):
    """
    @notice Unwind a credit account using an Aave flash loan.
    @dev Requires bAsset approval to sell the unlocked collateral.
    @param min_out Minimum amount of reserve returned to the user after unwind.
    @param amount Amount of reserve to flash loan for a partial unwind.
    @return Amount of reserve recovered and the post credit account state.
    """
    account: CreditAccount = staticcall credt.getCreditAccount(msg.sender)
    debt: uint256 = min(account.credit, amount)
    assert debt > 0  # dev: no debt

    balance_before: uint256 = staticcall reserve.balanceOf(self)
    extcall aave_pool.flashLoanSimple(self, reserve.address, debt, abi_encode(msg.sender), 0)
    output: uint256 = staticcall reserve.balanceOf(self) - balance_before

    assert output >= min_out  # dev: insufficient output
    extcall reserve.transfer(msg.sender, output)

    return output, staticcall credt.getCreditAccount(msg.sender)


@external
def executeOperation(
    asset: address,
    amount: uint256,
    premium: uint256,
    initiator: address,
    params: Bytes[128]
) -> bool:
    assert msg.sender == aave_pool.address  # dev: must come from aave pool
    assert initiator == self  # dev: must be self-initiated
    assert asset == reserve.address  # dev: must borrow reserve

    user: address = abi_decode(params, address)
    collateral: uint256 = extcall credit_facility.repay(user, amount)
    extcall basset.transferFrom(user, self, collateral)

    reserves_recovered: uint256 = self.sell_basset()
    amount_owed: uint256 = amount + premium
    assert staticcall reserve.balanceOf(self) >= amount_owed  # dev: insufficient repayment

    account: CreditAccount = staticcall credt.getCreditAccount(user)
    log Unwound(
        user=user,
        credit_repaid=amount,
        collateral_unlocked=collateral,
        reserve_recovered=reserves_recovered,
        reserve_spent_on_flash=amount_owed,
        remaining_credit=account.credit,
        remaining_collateral=account.collateral,
    )

    return True


@internal
def buy_basset():
    amount: uint256 = staticcall reserve.balanceOf(self)
    params: ExactInputSingleParams = ExactInputSingleParams(
        token_in=reserve.address,
        token_out=basset.address,
        fee=staticcall credit_facility.feeTier(),
        recipient=self,
        deadline=block.timestamp,
        amount_in=amount,
        amount_out_minimum=0,
        sqrt_price_limit_x96=0,
    )
    extcall router.exactInputSingle(params)


@internal
def sell_basset() -> uint256:
    amount: uint256 = staticcall basset.balanceOf(self)
    params: ExactInputSingleParams = ExactInputSingleParams(
        token_in=basset.address,
        token_out=reserve.address,
        fee=staticcall credit_facility.feeTier(),
        recipient=self,
        deadline=block.timestamp,
        amount_in=amount,
        amount_out_minimum=0,
        sqrt_price_limit_x96=0,
    )
    return extcall router.exactInputSingle(params)
