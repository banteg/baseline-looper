import pytest

BASE_YES_CREDIT_FACILITY = "0xc9329Cb681d1338219B9e21E5E99754853436C8D"
AAVE_V3_BASE_POOL = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
BASE_TX_GAS = 8_000_000


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
    return project.weth.at("0x4200000000000000000000000000000000000006")


@pytest.fixture
def yes(project):
    return project.ERC20.at("0x1B68244B100A6713ca7F540697b1bE12148a8bf9")


@pytest.fixture
def looper(project, dev):
    return project.Looper.deploy(
        BASE_YES_CREDIT_FACILITY,
        AAVE_V3_BASE_POOL,
        sender=dev,
        gas=BASE_TX_GAS,
    )


@pytest.fixture
def credt(project):
    return project.CREDTv1.at("0xa35E4Ac9565Fb006812755C30c369314be3511D9")


@pytest.fixture
def credit_facility(project):
    return project.CreditFacility.at(BASE_YES_CREDIT_FACILITY)


@pytest.fixture
def router(project, credit_facility):
    return project.router.at(credit_facility.router())
