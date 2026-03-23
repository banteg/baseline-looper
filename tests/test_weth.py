from ape import convert
import pytest

BASE_TX_GAS = 100_000


@pytest.mark.skip(reason="Base WETH predeploy withdraw reverts on the Ape/Anvil Base fork")
def test_weth(weth, dev):
    weth.deposit(value="1 ether", sender=dev, gas=BASE_TX_GAS)
    assert weth.balanceOf(dev) == convert("1 ether", int)
    weth.withdraw("1 ether", sender=dev, gas=BASE_TX_GAS)
    assert weth.balanceOf(dev) == 0
