# -*- coding: utf-8 -*-
"""Read a YAML control file and generate all SLURM sbatchs scripts to orchestrate a workflow."""
import click
import logging
import os
import pathlib
import re
import sys

from datetime import datetime
from pathlib import Path
from rich.console import Console
from typing import Optional

from . import constants
from .file_utils import check_infile_status, backup_file
from .console_helper import print_yellow, print_red, print_green
from .builder import Builder as WorkflowBuilder


error_console = Console(stderr=True, style="bold red")

console = Console()


DEFAULT_OUTDIR = os.path.join(
    constants.DEFAULT_OUTDIR_BASE,
    os.path.splitext(os.path.basename(__file__))[0],
    constants.DEFAULT_TIMESTAMP
)


def validate_verbose(ctx, param, value):
    """Validate the validate option.

    Args:
        ctx (Context): The click context.
        param (str): The parameter.
        value (bool): The value.

    Returns:
        bool: The value.
    """

    if value is None:
        click.secho("--verbose was not specified and therefore was set to 'True'", fg='yellow')
        return constants.DEFAULT_VERBOSE
    return value


@click.command()
@click.option('--control_file', help='Required: The YAML file that contains all of the info required to create the SLURM workflow shell scripts.')
@click.option('--logfile', help="Optional: The log file")
@click.option('--outdir', help=f"Optional: The default is the current working directory - default is '{DEFAULT_OUTDIR}'")
@click.option('--verbose', is_flag=True, help=f"Will print more info to STDOUT - default is '{constants.DEFAULT_VERBOSE}'.", callback=validate_verbose)
def main(
    control_file: str,
    logfile: Optional[str],
    outdir: Optional[str],
    verbose: Optional[bool]
    ):
    """Read a YAML control file and generate all SLURM sbatchs scripts to orchestrate a workflow."""
    error_ctr = 0

    if control_file is None:
        print_red("--control_file was not specified")
        error_ctr += 1

    if error_ctr > 0:
        print_red("Required parameter(s) not defined")
        click.echo(click.get_current_context().get_help())
        sys.exit(1)

    check_infile_status(control_file, "yaml")

    if outdir is None:
        outdir = DEFAULT_OUTDIR
        print_yellow(f"--outdir was not specified and therefore was set to '{outdir}'")

    if not os.path.exists(outdir):
        pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
        print_yellow(f"Created output directory '{outdir}'")

    if logfile is None:
        logfile = os.path.join(
            outdir,
            os.path.splitext(os.path.basename(__file__))[0] + '.log'
        )
        print_yellow(f"--logfile was not specified and therefore was set to '{logfile}'")

    if verbose is None:
        verbose = constants.DEFAULT_VERBOSE
        print_yellow(f"--verbose was not specified and therefore was set to '{verbose}'")


    logging.basicConfig(
        filename=logfile,
        format=constants.DEFAULT_LOGGING_FORMAT,
        level=constants.DEFAULT_LOGGING_LEVEL
    )

    builder = WorkflowBuilder(
        control_file=control_file,
        logfile=logfile,
        outdir=outdir,
        verbose=verbose
    )

    builder.build()

    if verbose:
        console.print(f"The log file is '{logfile}'.")
        print_green(f"Execution of '{os.path.abspath(__file__)}' completed.")

if __name__ == '__main__':
    main()
