import click
from wiki import create_app


@click.command()
@click.option('--debug/--no-debug', envvar='WIKI_DEBUG', default=True)
def main(debug):
    app = create_app()
    if debug:
        click.echo("Running wiki in debug mode!")
        app.run()
    # TODO: implement non-debug mode (lol)
