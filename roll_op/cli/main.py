import typer
import roll_op.confgen as confgen
import os

app = typer.Typer(name="roll-op")


@app.callback()
def callback():
    """
    Simple OP Stack Rollup

    Main CLI arguments (ones that come before the subcommand) are defined here.
    """


@app.command()
def config(
    datadir: str = typer.Option(
        help="Directory in which to place configuration files", default=None
    ),
    layer1: bool = typer.Option(
        help="Specify if deploying your own layer1", default=None
    ),
):
    """
    Generate the configuration for your OP Stack Rollup
    """
    if datadir is None:
        home_directory = os.path.expanduser("~")
        datadir = typer.prompt(
            "Data directory for configuration files",
            default=f"{home_directory}/.roll-op/config",
        )
    if layer1 is None:
        layer1 = typer.confirm("Are you deploying your own layer1?")

    confgen.generate(datadir, layer1)
