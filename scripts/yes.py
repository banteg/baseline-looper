from datetime import datetime
import os

import click
import toolstr
from ape import accounts, project
from ape.cli import ConnectedProviderCommand

BASE_YES_CREDIT_FACILITY = "0xc9329Cb681d1338219B9e21E5E99754853436C8D"
AAVE_V3_BASE_POOL = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
BASE_TX_GAS = 8_000_000


@click.group
def cli():
    pass


def show_credit_account(acc):
    expiry = datetime.utcfromtimestamp(acc.expiry) if acc.expiry else "none"
    toolstr.print_table(
        [
            ["credit, eth", acc.credit / 1e18],
            ["collateral, yes", acc.collateral / 1e18],
            ["expiry", expiry],
        ],
        labels=["name", "value"],
    )


def get_account(is_fork):
    if is_fork:
        return accounts.test_accounts[0]

    return accounts.load(
        click.prompt("ape account", type=click.Choice(list(accounts.aliases)))
    )


def get_credit_facility():
    return project.CreditFacility.at(BASE_YES_CREDIT_FACILITY)


def get_looper(is_fork, deployer):
    if is_fork:
        return project.Looper.deploy(
            BASE_YES_CREDIT_FACILITY,
            AAVE_V3_BASE_POOL,
            sender=deployer,
            gas=BASE_TX_GAS,
        )

    looper_address = os.environ.get("LOOPER_ADDRESS")
    if looper_address is None:
        looper_address = click.prompt("looper address")
    return project.Looper.at(looper_address)


@cli.command(cls=ConnectedProviderCommand)
def deploy(network):
    is_fork = "-fork" in network.name
    deployer = get_account(is_fork)
    if is_fork:
        looper = get_looper(True, deployer)
    else:
        looper = project.Looper.deploy(
            BASE_YES_CREDIT_FACILITY,
            AAVE_V3_BASE_POOL,
            sender=deployer,
            gas=BASE_TX_GAS,
        )
    print(looper.address)


@cli.command(cls=ConnectedProviderCommand)
def loop(network):
    is_fork = "-fork" in network.name
    user = get_account(is_fork)

    credit_facility = get_credit_facility()
    credt = project.CREDTv1.at(credit_facility.CREDT())
    weth = project.weth.at(credit_facility.reserve())
    basset = project.ERC20.at(credit_facility.bAsset())
    router = project.router.at(credit_facility.router())
    looper = get_looper(is_fork, user)
    print(user)

    credit_account = credt.getCreditAccount(user)
    show_credit_account(credit_account)

    eth_balance = user.balance
    eth_fmt = toolstr.format(eth_balance / 1e18)
    weth_balance = weth.balanceOf(user)
    weth_fmt = toolstr.format(weth_balance / 1e18)

    wrap_amount = click.prompt(
        f"you have {eth_fmt} eth and {weth_fmt} weth. type how much eth you want to wrap.",
        type=click.FloatRange(min=0, max=eth_balance / 1e18, clamp=True),
    )
    if wrap_amount > 0:
        click.secho(f"wrapping {wrap_amount} eth into weth", fg="green")
        weth.deposit(value=int(wrap_amount * 1e18), sender=user)

    weth_balance = weth.balanceOf(user)
    weth_fmt = toolstr.format(weth_balance / 1e18)

    amount = click.prompt(
        f"how much weth to loop? you have {weth_fmt} weth",
        type=click.FloatRange(min=0, max=weth_balance / 1e18, clamp=True),
        default=weth_balance / 1e18,
    )

    weth_allowance = weth.allowance(user, looper)
    if weth_allowance == 0:
        click.secho("approve looper to pull your weth", fg="green")
        weth.approve(looper, 2**256 - 1, sender=user, gas=BASE_TX_GAS)

    num_loops = click.prompt(
        "how many loops?", type=click.IntRange(min=1, max=69), default=8
    )
    add_days = click.prompt(
        "how many days to add to the credit account? set 0 if you already have a position.",
        type=click.IntRange(0, 365),
        default=30 if credit_account.expiry == 0 else 0,
    )
    if not click.confirm(
        f"loop {amount} weth for {num_loops} times and add {add_days} days, correct?"
    ):
        return

    click.secho("looping in", fg="green")
    looper.loop(int(amount * 1e18), num_loops, add_days, sender=user, gas=BASE_TX_GAS)

    credit_account = credt.getCreditAccount(user)
    show_credit_account(credit_account)
    print(f"wallet yes balance: {toolstr.format(basset.balanceOf(user) / 1e18)}")
    print(f"router fee tier: {credit_facility.feeTier()}")


@cli.command(cls=ConnectedProviderCommand)
def unwind(network):
    is_fork = "-fork" in network.name
    user = get_account(is_fork)

    credit_facility = get_credit_facility()
    credt = project.CREDTv1.at(credit_facility.CREDT())
    weth = project.weth.at(credit_facility.reserve())
    yes = project.ERC20.at(credit_facility.bAsset())
    looper = get_looper(is_fork, user)
    print(user)

    credit_account = credt.getCreditAccount(user)
    show_credit_account(credit_account)
    assert credit_account.credit > 0, "nothing to unwind"

    if yes.allowance(user, looper) < credit_account.collateral:
        click.secho("approve looper to pull your yes", fg="green")
        yes.approve(looper, 2**256 - 1, sender=user, gas=BASE_TX_GAS)

    unwind_divisor = click.prompt(
        "repay what fraction of current credit? use 1 for full, 3 for one-third",
        type=click.IntRange(min=1),
        default=1,
    )
    repay_amount = credit_account.credit // unwind_divisor

    if unwind_divisor == 1:
        output, post_credit = looper.unwind.call(0, sender=user)
    else:
        output, post_credit = looper.unwind.call(0, repay_amount, sender=user)

    output_fmt = toolstr.format(output / 1e18)
    print(f"the contract can unwind {output_fmt} weth from your position")
    show_credit_account(post_credit)
    print("flash loan fee: Aave premium only")
    if not click.confirm("does this sound good?"):
        return

    min_output = int(output * 0.995)
    weth_a = weth.balanceOf(user)
    if unwind_divisor == 1:
        looper.unwind(min_output, sender=user, gas=BASE_TX_GAS)
    else:
        looper.unwind(min_output, repay_amount, sender=user, gas=BASE_TX_GAS)
    weth_b = weth.balanceOf(user)
    weth_diff_fmt = toolstr.format((weth_b - weth_a) / 1e18)
    print(f"recovered {weth_diff_fmt} weth")
