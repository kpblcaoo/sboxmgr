"""CLI command: export config as standardized JSON"""

import typer

app = typer.Typer(help="Export configurations in standardized formats")

@app.command()
def json():
    """Export configuration as JSON."""
    typer.echo("JSON export functionality - coming soon!")

@app.command()
def yaml():
    """Export configuration as YAML."""
    typer.echo("YAML export functionality - coming soon!")

if __name__ == "__main__":
    app()
