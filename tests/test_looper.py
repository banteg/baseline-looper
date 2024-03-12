import pytest
import toolstr
import ape


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
def test_loop_borrow(weth, yes, router, looper, baseline, dev, user, whale, profitable):
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
    looper.loop("10 ether", 10, 30, 0, sender=user)
    print_status()

    # a whale buys yes
    if profitable:
        weth.deposit(value="1000 ether", sender=whale)
        weth.approve(router, 2**256 - 1, sender=whale)
        router.exactInputSingle(
            [weth, yes, 10000, whale, 2**256 - 1, weth.balanceOf(whale), 0, 0],
            sender=whale,
        )

    yes.approve(looper, 2**256 - 1, sender=user)
    looper.unwind(0, sender=user)
    print_status()

    print(yes.balanceOf(dev) / 1e18, "fees")


def test_double_wind(weth, looper, user, baseline, yes):
    weth.deposit(value="100 ether", sender=user)
    weth.approve(looper, 2**256 - 1, sender=user)
    for i in range(1, 4):
        looper.loop("10 ether", i, 30 if i == 1 else 0, 0, sender=user)
