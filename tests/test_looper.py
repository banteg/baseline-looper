import pytest
import toolstr

BASE_TX_GAS = 8_000_000


def test_borrow(weth, yes, router, credt, credit_facility, user):
    weth.deposit(value="5 ether", sender=user)

    weth.approve(router, 2**256 - 1, sender=user)
    router.exactInputSingle(
        [weth, yes, credit_facility.feeTier(), user, 2**256 - 1, weth.balanceOf(user), 0, 0],
        sender=user,
        gas=BASE_TX_GAS,
    )
    bassets = yes.balanceOf(user)
    print(f"bought {bassets / 1e18} yes")

    yes.approve(credit_facility, 2**256 - 1, sender=user, gas=BASE_TX_GAS)
    credit_facility.borrow(user, bassets, 30, sender=user, gas=BASE_TX_GAS)

    debt = weth.balanceOf(user)
    print(f"borrow {debt / 1e18} weth")
    credit = credt.getCreditAccount(user)
    assert credit.collateral == bassets
    assert credit.credit >= debt


@pytest.mark.parametrize("divisor", [1, 3])
def test_loop_then_unwind(weth, yes, looper, credt, user, divisor):
    def print_status(acc=None):
        if acc is None:
            acc = credt.getCreditAccount(user)
        toolstr.print_table(
            [
                ["credit", acc.credit / 1e18],
                ["collateral", acc.collateral / 1e18],
                ["weth balance", weth.balanceOf(user) / 1e18],
                ["yes balance", yes.balanceOf(user) / 1e18],
            ]
        )

    weth.deposit(value="20 ether", sender=user)
    weth.approve(looper, 2**256 - 1, sender=user, gas=BASE_TX_GAS)
    looper.loop("2 ether", 3, 7, sender=user, gas=BASE_TX_GAS)
    print_status()

    pre_acc = credt.getCreditAccount(user)
    yes.approve(looper, 2**256 - 1, sender=user, gas=BASE_TX_GAS)
    weth_before = weth.balanceOf(user)

    if divisor == 1:
        output, simulated_post = looper.unwind.call(0, sender=user)
        looper.unwind(output * 99 // 100, sender=user, gas=BASE_TX_GAS)
    else:
        repay_amount = pre_acc.credit // divisor
        output, simulated_post = looper.unwind.call(0, repay_amount, sender=user)
        looper.unwind(output * 99 // 100, repay_amount, sender=user, gas=BASE_TX_GAS)

    print("output", toolstr.format(output / 1e18))
    print_status(simulated_post)

    assert output > 0
    assert weth.balanceOf(user) >= weth_before + output

    post_acc = credt.getCreditAccount(user)
    if divisor == 1:
        assert post_acc.credit == 0
        assert post_acc.collateral == 0
    else:
        assert post_acc.credit < pre_acc.credit
        assert post_acc.collateral < pre_acc.collateral


def test_double_wind(weth, looper, user):
    weth.deposit(value="20 ether", sender=user)
    weth.approve(looper, 2**256 - 1, sender=user, gas=BASE_TX_GAS)
    for i in range(1, 4):
        looper.loop("2 ether", i, 30 if i == 1 else 0, sender=user, gas=BASE_TX_GAS)
