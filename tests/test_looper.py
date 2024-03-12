import pytest
import toolstr


@pytest.mark.skip()
def test_borrow(weth, yes, router, looper, baseline, dev):
    # tx = looper.flash(value=10**18 // 10_000, sender=dev)
    # tx.show_trace()

    # eth to weth
    weth.deposit(value="10 ether", sender=dev)

    # buy yes
    weth.approve(router, 2**256 - 1, sender=dev)
    out = router.exactInputSingle(
        [
            weth,
            yes,
            10000,
            dev,
            2**256 - 1,
            weth.balanceOf(dev),
            0,  # min amount out
            0,
        ],
        sender=dev,
    )
    bassets = yes.balanceOf(dev)
    print(f"bought {bassets / 1e18} yes")

    # borrow weth
    yes.approve(baseline, 2**256 - 1, sender=dev)
    baseline.borrow(dev, bassets, 30, sender=dev)

    debt = weth.balanceOf(dev)
    print(f"borrow {debt / 1e18} weth")


def test_loop_borrow(weth, yes, router, looper, baseline, dev):
    def print_status():
        acc = baseline.getCreditAccount(dev)
        toolstr.print_table(
            [
                ["principal", acc.principal / 1e18],
                ["collateral", acc.collateral / 1e18],
                ["interest", acc.interest / 1e18],
                ["weth balance", weth.balanceOf(dev) / 1e18],
                ["yes balance", yes.balanceOf(dev) / 1e18],
            ]
        )

    weth.deposit(value="100 ether", sender=dev)
    weth.approve(looper, 2**256 - 1, sender=dev)
    looper.loop("10 ether", 30, 10, sender=dev)
    print_status()

    yes.approve(looper, 2**256 - 1, sender=dev)
    tx = looper.unwind(sender=dev)
    tx.show_trace()
    print_status()

    print(yes.balanceOf(looper) / 1e18, "recovered")