from ape import convert
import pytest


@pytest.mark.skip()
def test_weth(weth, dev):
    weth.deposit(value="1 ether", sender=dev)
    assert weth.balanceOf(dev) == convert("1 ether", int)
    weth.withdraw("1 ether", sender=dev)
    assert weth.balanceOf(dev) == 0
