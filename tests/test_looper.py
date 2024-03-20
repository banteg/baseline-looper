import pytest
import toolstr
from math import sqrt

Q96 = 2**96


def test_borrow(weth, yes, router, looper, baseline, user):
    # eth to weth
    weth.deposit(value="10 ether", sender=user)

    # buy yes
    weth.approve(router, 2**256 - 1, sender=user)
    router.exactInputSingle(
        [weth, yes, 10000, user, 2**256 - 1, weth.balanceOf(user), 0, 0],
        sender=user,
    )
    bassets = yes.balanceOf(user)
    print(f"bought {bassets / 1e18} yes")

    # borrow weth
    yes.approve(baseline, 2**256 - 1, sender=user)
    baseline.borrow(user, bassets, 30, sender=user)

    debt = weth.balanceOf(user)
    print(f"borrow {debt / 1e18} weth")


@pytest.mark.parametrize("profitable", [True, False])
def test_loop_borrow(
    weth, yes, router, quoter, looper, baseline, dev, user, whale, profitable
):
    def print_status():
        acc = baseline.getCreditAccount(user)
        toolstr.print_table(
            [
                ["principal", acc.principal / 1e18],
                ["collateral", acc.collateral / 1e18],
                ["interest", acc.interest / 1e18],
                ["weth balance", weth.balanceOf(user) / 1e18],
                ["yes balance", yes.balanceOf(user) / 1e18],
            ]
        )

    weth.deposit(value="100 ether", sender=user)
    weth.approve(looper, 2**256 - 1, sender=user)
    looper.loop("10 ether", 10, 7, sender=user)
    print_status()

    # whale causes a shift
    if profitable:
        floor_tick = baseline.floorTick()
        taget_tick = baseline.checkpointTick() + 1000
        taget_q96 = int(sqrt(1.0001**taget_tick) * Q96)
        quote = quoter.quoteExactOutputSingle.call(
            (weth, yes, 2**128, 10000, taget_q96)
        )
        weth.deposit(value=quote.amountIn, sender=whale)
        weth.approve(router, 2**256 - 1, sender=whale)
        router.exactInputSingle(
            [weth, yes, 10000, whale, 2**256 - 1, weth.balanceOf(whale), 0, 0],
            sender=whale,
        )
        receipt = baseline.rebalance(sender=whale)
        assert baseline.floorTick() > floor_tick, "not shifted"

    yes.approve(looper, 2**256 - 1, sender=user)
    output = looper.unwind.call(0, sender=user)
    print("output", toolstr.format(output / 1e18))
    receipt = looper.unwind(output, sender=user)
    print(list(receipt.decode_logs(baseline.Borrow)))
    print_status()


def test_double_wind(weth, looper, user, baseline, yes):
    weth.deposit(value="100 ether", sender=user)
    weth.approve(looper, 2**256 - 1, sender=user)
    for i in range(1, 4):
        looper.loop("10 ether", i, 30 if i == 1 else 0, sender=user)
