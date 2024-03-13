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


@cli.command(cls=ConnectedProviderCommand)
def loop():
    baseline = project.baseline.at("0x14eB8d9b6e19842B5930030B18c50B0391561f27")
    weth = project.weth.at("0x4300000000000000000000000000000000000004")
    yes = project.basset.at("0x20fE91f17ec9080E3caC2d688b4EcB48C5aC3a9C")
    router = project.router.at("0x337827814155ECBf24D20231fCA4444F530C0555")
    quoter = project.quoter.at("0x3b299f65b47c0bfAEFf715Bc73077ba7A0a685bE")
    # TODO: replace w a production contract
    looper = project.Looper.deploy(sender=accounts.test_accounts[0])

    # user = accounts.load(
    #     click.prompt("ape account", type=click.Choice(list(accounts.aliases)))
    # )
    user = accounts.test_accounts[1]
    print(user)

    credit_account = baseline.getCreditAccount(user)
    show_credit_account(credit_account)

    eth_balance = user.balance
    eth_fmt = toolstr.format(eth_balance / 1e18)
    weth_balance = weth.balanceOf(user)
    weth_fmt = toolstr.format(weth_balance / 1e18)

    wrap_amount = click.prompt(
        f"you have {eth_fmt} eth and {weth_fmt} weth. the contract accepts weth. type how much eth you want to wrap.",
        type=click.FloatRange(min=0, max=eth_balance / 1e18),
        default=100,
    )
    if wrap_amount > 0:
        click.secho(f"wrapping {wrap_amount} eth into weth", fg="green")
        weth.deposit(value=int(wrap_amount * 1e18), sender=user)

    weth_balance = weth.balanceOf(user)
    weth_fmt = toolstr.format(weth_balance / 1e18)

    amount = click.prompt(
        f"how much to ape ser? you have {weth_fmt} weth",
        type=click.FloatRange(min=0, max=weth_balance / 1e18),
        default=100,
    )

    weth_allowance = weth.allowance(user, looper)
    if weth_allowance == 0:
        click.secho("approve looper to pull your weth", fg="green")
        weth.approve(looper, 2**256 - 1, sender=user)

    num_loops = click.prompt(
        "how many times to loop ser?", type=click.IntRange(min=1, max=69), default=5
    )
    add_days = click.prompt(
        "how many days to add to the credit account? you can set to 0 if you already have a position.",
        type=click.IntRange(0, 365),
        default=30,
    )
    if not click.confirm(
        f"loop {amount} weth for {num_loops} times and add {add_days} days, correct?"
    ):
        return

    click.secho(f"looping", fg="green")
    # TODO slippage calc
    acc_after = looper.loop.call(
        int(amount * 1e18), num_loops, add_days, 0, sender=user
    )
    tokens_bought = acc_after.collateral - credit_account.collateral
    print("tokens bought", toolstr.format(tokens_bought / 1e18))
    res = quoter.quoteExactOutputSingle.call((weth, yes, tokens_bought, 10000, 0))
    limit_price = res.sqrtPriceX96After
    # print("price", (limit_price / 2**96) ** 2)
    # show_credit_account(acc_after)
    limit_price = int(((limit_price / 2**96) ** 2 * 1.01) ** 0.5 * 2**96)
    looper.loop(int(amount * 1e18), num_loops, add_days, limit_price, sender=user)
    credit_account = baseline.getCreditAccount(user)
    show_credit_account(credit_account)


@cli.command(cls=ConnectedProviderCommand)
def unwind():
    pass
