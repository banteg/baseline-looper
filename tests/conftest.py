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
    return project.BPOOLv1.at("0x1a49351bdB4BE48C0009b661765D01ed58E8C2d8")


@pytest.fixture
def looper(project, dev):
    return project.Looper.deploy(dev, sender=dev)


@pytest.fixture
def credt(project):
    return project.CREDTv1.at("0x158d9270F7931d0eB48Efd72E62c0E9fFfE0E67b")


@pytest.fixture
def credit_facility(project):
    return project.CreditFacility.at("0xd7E6ad255B3Ca48b2E15705Cc66FDa21eB58745a")


@pytest.fixture
def router(project):
    return project.router.at("0x337827814155ECBf24D20231fCA4444F530C0555")


@pytest.fixture
def quoter(project):
    return project.quoter.at("0x3b299f65b47c0bfAEFf715Bc73077ba7A0a685bE")
