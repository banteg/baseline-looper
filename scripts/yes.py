from datetime import datetime
import click
import toolstr
from ape import accounts, project
from ape.cli import ConnectedProviderCommand


@click.group
def cli():
    pass


def show_credit_account(acc):
    toolstr.print_table(
        [
            ["principal, eth", acc.principal / 1e18],
            ["interest, eth", acc.interest / 1e18],
            ["collateral, yes", acc.collateral / 1e18],
            ["expiry", datetime.utcfromtimestamp(acc.expiry)],
            ["last floor, eth", acc.lastFloor / 1e18],
        ],
        labels=["name", "value"],
    )


def get_account(is_fork):
    if is_fork:
        return accounts.test_accounts[0]
    else:
        return accounts.load(
            click.prompt("ape account", type=click.Choice(list(accounts.aliases)))
        )


def get_looper(is_fork):
    if is_fork:
        return project.Looper.deploy(sender=accounts.test_accounts[0])
    else:
        raise NotImplementedError("deployment tbd")


@cli.command(cls=ConnectedProviderCommand)
def loop(network):
    is_fork = "-fork" in network.name
    baseline = project.baseline.at("0x14eB8d9b6e19842B5930030B18c50B0391561f27")
    weth = project.weth.at("0x4300000000000000000000000000000000000004")
    looper = get_looper(is_fork)
    user = get_account(is_fork)
    print(user)

    credit_account = baseline.getCreditAccount(user)
    show_credit_account(credit_account)

    eth_balance = user.balance
    eth_fmt = toolstr.format(eth_balance / 1e18)
    weth_balance = weth.balanceOf(user)
    weth_fmt = toolstr.format(weth_balance / 1e18)

    wrap_amount = click.prompt(
        f"you have {eth_fmt} eth and {weth_fmt} weth. the contract accepts weth. type how much eth you want to wrap.",
        type=click.FloatRange(min=0, max=eth_balance / 1e18, clamp=True),
    )
    if wrap_amount > 0:
        click.secho(f"wrapping {wrap_amount} eth into weth", fg="green")
        weth.deposit(value=int(wrap_amount * 1e18), sender=user)

    weth_balance = weth.balanceOf(user)
    weth_fmt = toolstr.format(weth_balance / 1e18)

    amount = click.prompt(
        f"how much to ape ser? you have {weth_fmt} weth",
        type=click.FloatRange(min=0, max=weth_balance / 1e18, clamp=True),
        default=weth_balance / 1e18,
    )

    weth_allowance = weth.allowance(user, looper)
    if weth_allowance == 0:
        click.secho("approve looper to pull your weth", fg="green")
        weth.approve(looper, 2**256 - 1, sender=user)

    num_loops = click.prompt(
        "how many times to loop ser?", type=click.IntRange(min=1, max=69), default=8
    )
    add_days = click.prompt(
        "how many days to add to the credit account? you can set to 0 if you already have a position.",
        type=click.IntRange(0, 365),
        default=30 if credit_account.expiry == 0 else 0,
    )
    if not click.confirm(
        f"loop {amount} weth for {num_loops} times and add {add_days} days, correct?"
    ):
        return

    click.secho("looping in", fg="green")
    looper.loop(int(amount * 1e18), num_loops, add_days, sender=user)

    credit_account = baseline.getCreditAccount(user)
    show_credit_account(credit_account)


@cli.command(cls=ConnectedProviderCommand)
def unwind(network):
    is_fork = "-fork" in network.name
    baseline = project.baseline.at("0x14eB8d9b6e19842B5930030B18c50B0391561f27")
    weth = project.weth.at("0x4300000000000000000000000000000000000004")
    yes = project.basset.at("0x20fE91f17ec9080E3caC2d688b4EcB48C5aC3a9C")
    looper = get_looper(is_fork)
    user = get_account(is_fork)
    print(user)

    credit_account = baseline.getCreditAccount(user)
    show_credit_account(credit_account)
    assert credit_account.principal > 0, "nothing to unwind"

    if yes.allowance(user, looper) < credit_account.collateral:
        click.secho("approve looper to pull your yes", fg="green")
        yes.approve(looper, 2**256 - 1, sender=user)

    output = looper.unwind.call(0, sender=user)
    output_fmt = toolstr.format(output / 1e18)
    print(f"the contract can unwind {output_fmt} weth from your position")
    print("service fee: 0.1%, flash loan fee: 0.01%")
    if not click.confirm("does this sound good?"):
        return

    min_output = int(output * 0.995)
    weth_a = weth.balanceOf(user)
    looper.unwind(min_output, sender=user)
    weth_b = weth.balanceOf(user)
    weth_diff_fmt = toolstr.format((weth_b - weth_a) / 1e18)
    print(f"recovered {weth_diff_fmt} weth")
