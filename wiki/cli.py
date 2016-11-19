"""
    CLI
    ~~~
"""
import os

import click
from wiki.web import create_app

@click.group()
@click.option('--directory', type=click.Path(exists=True), default=None)
@click.pass_context
def main(ctx, directory):
    """
        Base setup for all the following commands.

        \b
        :param str directory: the directory to run wiki in, optional.
            If no directory is provided the current directory will be
            used.
    """
    if not directory:
        directory = os.getcwd()
    ctx.meta['directory'] = os.path.abspath(click.format_filename(directory))


@main.command()
@click.option('--debug/--no-debug', envvar='WIKI_DEBUG', default=False)
@click.pass_context
def web(ctx, debug):
    """
        Run the web app.

        \b
        :param bool debug: whether or not to run the web app in debug
            mode.
    """
    app = create_app(ctx.meta['directory'])
    app.run(debug=debug)
