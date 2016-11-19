import os

import click
from wiki.web import create_app


@click.command()
@click.option('--debug/--no-debug', envvar='WIKI_DEBUG', default=True)
@click.option('--directory', default=None)
def main(directory, debug):
    if not directory:
        directory = os.getcwd()
    app = create_app(directory)
    if debug:
        click.echo("Running wiki in debug mode!")
        app.run(debug=True)
    # TODO: implement non-debug mode (lol)
