import pytest
import toolstr
from math import sqrt

Q96 = 2**96


def test_borrow(weth, yes, router, credt, credit_facility, user):
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
    yes.approve(credit_facility, 2**256 - 1, sender=user)
    credit_facility.borrow(user, bassets, 30, sender=user)

    debt = weth.balanceOf(user)
    print(f"borrow {debt / 1e18} weth")
    credit = credt.getCreditAccount(user)
    assert credit.collateral == bassets
    assert credit.credit > debt
    print(credit)
    print("interest", (credit.credit - debt) / 1e18)


@pytest.mark.parametrize("partial", [True, False])
def test_loop_borrow(weth, yes, looper, credt, credit_facility, user, partial):
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

    weth.deposit(value="100 ether", sender=user)
    weth.approve(looper, 2**256 - 1, sender=user)
    looper.loop("10 ether", 10, 7, sender=user)
    print_status()

    yes.approve(looper, 2**256 - 1, sender=user)
    if partial:
        output, post_acc = looper.unwind.call(0, "2 ether", sender=user)
        print_status(post_acc)
        receipt = looper.unwind(output, "2 ether", sender=user)
    else:
        output, post_acc = looper.unwind.call(0, sender=user)
        print_status(post_acc)
        receipt = looper.unwind(output, sender=user)

    print("output", toolstr.format(output / 1e18))
    print(list(receipt.decode_logs(credit_facility.Borrow)))
    print_status()


def test_double_wind(weth, looper, user):
    weth.deposit(value="100 ether", sender=user)
    weth.approve(looper, 2**256 - 1, sender=user)
    for i in range(1, 4):
        looper.loop("10 ether", i, 30 if i == 1 else 0, sender=user)
