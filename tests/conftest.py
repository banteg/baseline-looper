import pytest


@pytest.fixture
def dev(accounts):
    return accounts[0]


@pytest.fixture
def user(accounts):
    return accounts[1]


@pytest.fixture
def whale(accounts):
    return accounts[2]


@pytest.fixture
def weth(project):
    return project.weth.at("0x4300000000000000000000000000000000000004")


@pytest.fixture
def yes(project):
    return project.basset.at("0x20fE91f17ec9080E3caC2d688b4EcB48C5aC3a9C")


@pytest.fixture
def looper(project, dev):
    return project.Looper.deploy(dev, sender=dev)


@pytest.fixture
def baseline(project):
    return project.baseline.at("0x14eB8d9b6e19842B5930030B18c50B0391561f27")


@pytest.fixture
def router(project):
    return project.router.at("0x337827814155ECBf24D20231fCA4444F530C0555")


@pytest.fixture
def quoter(project):
    return project.quoter.at("0x3b299f65b47c0bfAEFf715Bc73077ba7A0a685bE")
