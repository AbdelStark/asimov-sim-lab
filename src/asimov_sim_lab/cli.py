"""CLI entrypoint for Asimov Sim Lab."""

import typer

app = typer.Typer(no_args_is_help=True, help="Spec-first CLI scaffold for Asimov Sim Lab.")


@app.callback()
def main() -> None:
    """Root command group for the scaffold CLI."""


@app.command()
def doctor() -> None:
    """Basic repo-health smoke command."""
    typer.echo("ok: asimov-sim-lab scaffold ready")
