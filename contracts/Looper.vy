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
    lastFloor: uint256


interface Weth:
    def deposit(): payable
    def withdraw(amount: uint256): nonpayable

interface FlashLoan:
    def flashLoanSimple(receiverAddress: address, asset: address, amount: uint256, params: Bytes[128], referralCode: uint16): nonpayable

interface Baseline:
    def borrow(user: address, amount: uint256, add_days: uint256) -> Borrow: nonpayable
    def repay(user: address, amount: uint256) -> uint256: nonpayable
    def getCreditAccount(user: address) -> CreditAccount: view

interface SwapRouter:
    def exactInputSingle(params: ExactInputSingleParams) -> uint256: payable

interface Blast:
    def configureClaimableGas(): nonpayable
    def configureGovernor(governor: address): nonpayable


pac: immutable(FlashLoan)
router: immutable(SwapRouter)
weth: immutable(ERC20)
yes: immutable(ERC20)
baseline: immutable(Baseline)
blast: immutable(Blast)
fee_recipient: immutable(address)

@external
def __init__():
    pac = FlashLoan(0xd2499b3c8611E36ca89A70Fda2A72C49eE19eAa8)
    router = SwapRouter(0x337827814155ECBf24D20231fCA4444F530C0555)
    weth = ERC20(0x4300000000000000000000000000000000000004)
    yes = ERC20(0x20fE91f17ec9080E3caC2d688b4EcB48C5aC3a9C)
    baseline = Baseline(0x14eB8d9b6e19842B5930030B18c50B0391561f27)
    blast = Blast(0x4300000000000000000000000000000000000002)
    fee_recipient = msg.sender

    # pac pulls weth on flash loan repay
    weth.approve(pac.address, max_value(uint256))
    # router pulls weth on swap
    weth.approve(router.address, max_value(uint256))
    # router pulls yes on swap
    yes.approve(router.address, max_value(uint256))
    # baseline pulls weth on repay
    weth.approve(baseline.address, max_value(uint256))
    # baseline pulls yes on borrow
    yes.approve(baseline.address, max_value(uint256))

    # blast specific
    blast.configureClaimableGas()
    blast.configureGovernor(msg.sender)


@payable
@external
def loop(amount: uint256, num_loops: uint256, add_days: uint256) -> CreditAccount:
    """
    @notice Loop with WETH. Buys YES and borrows WETH for a number of times.
    @dev Requires WETH approval to pull borrowed WETH multiple times.
    """
    assert num_loops > 0  # dev: min 1 loop
    assert num_loops < 70  # dev: max 69 loops
    days: uint256 = add_days
    borrow: Borrow = empty(Borrow)

    weth.transferFrom(msg.sender, self, amount)
    self.buy_yes()

    for i in range(70):
        if i == num_loops:
            break
        if i == 1:
            days = 0
        borrow = baseline.borrow(msg.sender, yes.balanceOf(self), days)
        if i < num_loops - 1:
            weth.transferFrom(msg.sender, self, borrow.principal)
            self.buy_yes()

    return baseline.getCreditAccount(msg.sender)


@external
def unwind(min_out: uint256) -> uint256:
    """
    @notice Unwind a credit account using a flash loan. Allows unwinding underwater positions.
    @dev
        Requires YES approval to sell the unlocked collateral.
        Requires WETH approval if YES sell proceeds are unable to repay the principal.
    @param min_out Minimum amount of WETH returened to the user after unwind.
    @return output Amount of WETH recovered.
    """
    account: CreditAccount = baseline.getCreditAccount(msg.sender)
    debt: uint256 = account.principal + account.interest
    assert debt > 0  # dev: no debt
    pac.flashLoanSimple(self, weth.address, debt, _abi_encode(msg.sender), 0)
    output: uint256 = weth.balanceOf(self)
    assert output >= min_out  # dev: insufficient output
    weth.transfer(msg.sender, output)
    return output


@external
def executeOperation(asset: address, amount: uint256, premium: uint256, initiator: address, params: Bytes[128]) -> bool:
    assert msg.sender == pac.address  # dev: must come from pac pool
    assert initiator == self  # dev: must be self-initiated
    user: address = _abi_decode(params, address)
    cash: uint256 = baseline.repay(user, amount)
    yes.transferFrom(user, self, cash)
    yes.transfer(fee_recipient, cash / 1000)  # 0.1% fee for unwind
    self.sell_yes()
    return True


@internal
def buy_yes():
    amount: uint256 = weth.balanceOf(self)
    params: ExactInputSingleParams = ExactInputSingleParams({
        token_in: weth.address,
        token_out: yes.address,
        fee: 10000,
        recipient: self,
        deadline: block.timestamp,
        amount_in: amount,
        amount_out_minimum: 0,
        sqrt_price_limit_x96: 0,
    })
    router.exactInputSingle(params)


@internal
def sell_yes():
    amount: uint256 = yes.balanceOf(self)
    params: ExactInputSingleParams = ExactInputSingleParams({
        token_in: yes.address,
        token_out: weth.address,
        fee: 10000,
        recipient: self,
        deadline: block.timestamp,
        amount_in: amount,
        amount_out_minimum: 0,
        sqrt_price_limit_x96: 0,
    })
    router.exactInputSingle(params)
