#!/usr/bin/env python

# chatbot Copyright (C) 2024 Ben Greene
"""CLI initiated python app"""

import click
import sys
import logging
import logging.config
from pydantic_yaml import to_yaml_str

from .config import ServiceConfig


# https://stackoverflow.com/questions/242485/starting-python-debugger-automatically-on-error
def interactivedebugger(type, value, tb):
    if hasattr(sys, "ps1") or not sys.stderr.isatty():
        # we are in interactive mode or we don't have a tty-like
        # device, so we call the default hook
        sys.__excepthook__(type, value, tb)
    else:
        import traceback
        import pdb

        # we are NOT in interactive mode, print the exception...
        traceback.print_exception(type, value, tb)
        print
        # ...then start the debugger in post-mortem mode.
        # pdb.pm() # deprecated
        pdb.post_mortem(tb)  # more "modern"


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, debug):
    """
    Service and tools for basic service
    """
    ctx.ensure_object(dict)

    ctx.obj["DEBUG"] = debug

    if debug:
        click.echo(f"Debug mode is {'on' if debug else 'off'}", err=True)
        sys.excepthook = interactivedebugger


# ------------- CLI commands go below here -------------

from chatbot.config import ServiceConfig


def shared_options(function):
    function = click.option("--config", required=True, type=click.File("rb"))(function)
    function = click.option("--secrets", required=True, type=click.Path(exists=True))(
        function
    )
    function = click.pass_context(function)
    return function


@cli.command()
@shared_options
def parse(ctx, config, secrets):
    """Parse a config"""
    from pydantic_yaml import to_yaml_str

    configObj: ServiceConfig = ServiceConfig.from_yaml(config.name, secrets)
    click.echo(configObj)

    click.echo(to_yaml_str(configObj))


@cli.command()
@shared_options
def start(ctx, config, secrets):
    """Start the service"""
    from chatbot import app_start

    configObj: ServiceConfig = ServiceConfig.from_yaml(config.name, secrets)

    # Load logging configuration from YAML file
    logging.config.dictConfig(configObj.logging)

    logger = logging.getLogger(__name__)
    print(to_yaml_str(configObj, indent=2))

    app_start(configObj)


# ------------- CLI commands above here -------------

if __name__ == "__main__":
    cli()
