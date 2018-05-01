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
@click.option('--host', envvar='WIKI_HOST', default=None)
@click.option('--port', envvar='WIKI_PORT', default=None, type=int)
@click.pass_context
def web(ctx, debug, host, port):
    """
        Run the web app.

        \b
        :param bool debug: whether or not to run the web app in debug
            mode.
        :param str host: Set the host to 0.0.0.0 to connect from outside. 
            The default is 127.0.0.1.
        :param int port: Set the listening port. The default is 5000.
    """
    app = create_app(ctx.meta['directory'])
    app.run(debug=debug, host=host, port=port)
