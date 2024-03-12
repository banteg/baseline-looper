# @version 0.3.10
# @author banteg
# @notice Leverage loop into YES or unwind your position without needing the WETH.
from vyper.interfaces import ERC20

struct Borrow:
    principal: uint256
    interest: uint256

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
    principal: uint256
    interest: uint256
    collateral: uint256
    expiry: uint256
    last_floor: uint256


interface Weth:
    def deposit(): payable
    def withdraw(amount: uint256): nonpayable

interface FlashLoan:
    def flashLoanSimple(receiverAddress: address, asset: address, amount: uint256, params: Bytes[128], referralCode: uint16): nonpayable

interface Baseline:
    def borrow(user: address, amount: uint256, add_days: uint256) -> Borrow: nonpayable
    def repay(user: address, amount: uint256) -> uint256: nonpayable
    def getCreditAccount(user: address) -> CreditAccount: view

interface UniswapRouter:
    def exactInputSingle(params: ExactInputSingleParams) -> uint256: payable

interface Blast:
    def configureClaimableGas(): nonpayable
    def configureGovernor(governor: address): nonpayable


PAC_POOL: constant(address) = 0xd2499b3c8611E36ca89A70Fda2A72C49eE19eAa8
ROUTER: constant(address) = 0x337827814155ECBf24D20231fCA4444F530C0555
WETH: constant(address) = 0x4300000000000000000000000000000000000004
YES: constant(address) = 0x20fE91f17ec9080E3caC2d688b4EcB48C5aC3a9C
BASELINE: constant(address) = 0x14eB8d9b6e19842B5930030B18c50B0391561f27
BLAST: constant(address) = 0x4300000000000000000000000000000000000002
UNWIND_FEE_BPS: constant(uint256) = 20
MAX_BPS: constant(uint256) = 10_000
fee_recipient: immutable(address)

@external
def __init__():
    weth: ERC20 = ERC20(WETH)
    yes: ERC20 = ERC20(YES)
    fee_recipient = msg.sender

    # pac pulls weth on flash loan repay
    weth.approve(PAC_POOL, max_value(uint256))
    # router pulls weth on swap
    weth.approve(ROUTER, max_value(uint256))
    # router pulls yes on swap
    yes.approve(ROUTER, max_value(uint256))
    # baseline pulls weth on repay
    weth.approve(BASELINE, max_value(uint256))
    # baseline pulls yes on borrow
    yes.approve(BASELINE, max_value(uint256))

    # blast specific
    blast: Blast = Blast(BLAST)
    blast.configureClaimableGas()
    blast.configureGovernor(msg.sender)


@payable
@external
def loop(amount: uint256, add_days: uint256, num_loops: uint256):
    """
    @notice Loop with WETH. Buys YES and borrows WETH for a number of times.
    @dev Requires WETH approval to pull borrowed WETH multiple times.
    """
    assert num_loops > 0  # dev: min 1 loop
    weth: ERC20 = ERC20(WETH)
    yes: ERC20 = ERC20(YES)
    baseline: Baseline = Baseline(BASELINE)
    days: uint256 = add_days
    borrow: Borrow = empty(Borrow)

    weth.transferFrom(msg.sender, self, amount)
    self.buy_yes()

    for i in range(20):
        if i == num_loops:
            break
        if i > 0:
            days = 0
        borrow = baseline.borrow(msg.sender, yes.balanceOf(self), days)
        if i < num_loops - 1:
            weth.transferFrom(msg.sender, self, borrow.principal)
            self.buy_yes()


@external
def unwind():
    """
    @notice Unwind a credit account using a flash loan. Allows unwinding underwater positions.
    @dev Requires WETH approval if YES sell proceeds are unable to repay the principal.
    """
    baseline: Baseline = Baseline(BASELINE)
    pac: FlashLoan = FlashLoan(PAC_POOL)

    account: CreditAccount = Baseline(BASELINE).getCreditAccount(msg.sender)
    debt: uint256 = account.principal + account.interest
    assert debt > 0  # dev: no debt
    pac.flashLoanSimple(self, WETH, debt, _abi_encode(msg.sender), 0)


@external
def executeOperation(asset: address, amount: uint256, premium: uint256, initiator: address, params: Bytes[128]) -> bool:
    assert msg.sender == PAC_POOL  # dev: must come from pac pool
    assert initiator == self  # dev: must be self-initiated

    baseline: Baseline = Baseline(BASELINE)
    weth: ERC20 = ERC20(WETH)
    yes: ERC20 = ERC20(YES)

    user: address = _abi_decode(params, address)
    cash: uint256 = baseline.repay(user, amount)
    yes.transferFrom(user, self, cash)
    yes.transfer(fee_recipient, cash * UNWIND_FEE_BPS / MAX_BPS)
    self.sell_yes()
    weth_balance: uint256 = weth.balanceOf(self)
    # pull additional weth from the user if yes sell proceeds are insufficient
    if amount + premium > weth_balance:
        weth.transferFrom(user, self, amount + premium - weth_balance)
    else:
        weth.transfer(user, weth_balance - amount - premium)

    return True


@internal
def buy_yes():
    amount: uint256 = ERC20(WETH).balanceOf(self)
    params: ExactInputSingleParams = ExactInputSingleParams({
        token_in: WETH,
        token_out: YES,
        fee: 10000,
        recipient: self,
        deadline: block.timestamp,
        amount_in: amount,
        amount_out_minimum: 0,
        sqrt_price_limit_x96: 0,
    })
    UniswapRouter(ROUTER).exactInputSingle(params)


@internal
def sell_yes():
    amount: uint256 = ERC20(YES).balanceOf(self)
    params: ExactInputSingleParams = ExactInputSingleParams({
        token_in: YES,
        token_out: WETH,
        fee: 10000,
        recipient: self,
        deadline: block.timestamp,
        amount_in: amount,
        amount_out_minimum: 0,
        sqrt_price_limit_x96: 0,
    })
    UniswapRouter(ROUTER).exactInputSingle(params)
