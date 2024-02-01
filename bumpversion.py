"""Helper script for bumping the version of the software."""
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import click

from datetime import datetime
from typing import Optional
from rich.console import Console

error_console = Console(stderr=True, style="bold red")

console = Console()

DEFAULT_PROJECT = os.path.basename(os.path.dirname(__file__))

DEFAULT_BUMPVERSION_CONFIG_FILE = os.path.join(
    os.getcwd(),
    ".bumpversion.cfg"
)

DEFAULT_PRE_COMMIT_HOOK_FILE = os.path.join(
    os.getcwd(),
    ".git",
    "hooks",
    "pre-commit"
)

DEFAULT_OUTDIR = os.path.join(
    "/tmp/",
    os.getenv("USER"),
    DEFAULT_PROJECT,
    os.path.splitext(os.path.basename(__file__))[0],
    str(datetime.today().strftime("%Y-%m-%d-%H%M%S")),
)

LOGGING_FORMAT = "%(levelname)s : %(asctime)s : %(pathname)s : %(lineno)d : %(message)s"

LOG_LEVEL = logging.INFO

DEFAULT_VERBOSE = True

DEFAULT_PROJECT_DIR = os.getcwd()

g_verbose = DEFAULT_VERBOSE

def backup_file(file: str = None) -> Optional[str]:
    """Backup a file."""
    if os.path.exists(file):
        print(f"Will backup file '{file}'")
        backup_file = file + ".bak"
        shutil.move(file, backup_file)
        print(f"Backed up '{file}' to '{backup_file}'")
        return backup_file
    else:
        print(f"{file} does not exist so will not backup it")
        return None

def restore_file(file: str = None) -> None:
    if os.path.exists(file):
        if not file.endswith(".bak"):
            raise Exception(f"File '{file}' does not end with '.bak'")
        file = file.rstrip(".bak")
        print(f"Will restore file '{file}'")
        backup_file = file + ".bak"
        shutil.move(backup_file, file)
        print(f"Restored '{backup_file}' to '{file}'")
    else:
        print(f"{file} does not exist so will not restore it")

def _execute_cmd(
    cmd: str,
    outdir: str = None,
    stdout_file: str = None,
    stderr_file: str = None,
    verbose: bool = DEFAULT_VERBOSE,
):
    """Execute a command via system call using the subprocess module
    :param cmd: {str} - the executable to be invoked
    :param outdir: {str} - the output directory where STDOUT, STDERR and the shell script should be written to
    :param stdout_file: {str} - the file to which STDOUT will be captured in
    :param stderr_file: {str} - the file to which STDERR will be captured in
    """
    if cmd is None:
        raise Exception("cmd was not specified")

    cmd = cmd.strip()

    logging.info(f"Will attempt to execute '{cmd}'")
    if verbose:
        print(f"Will attempt to execute '{cmd}'")

    if outdir is None:
        outdir = "/tmp"
        logging.info(
            f"outdir was not defined and therefore was set to default '{outdir}'"
        )

    if stdout_file is None:
        primary = cmd.split(" ")[0]
        basename = os.path.basename(primary)
        stdout_file = os.path.join(outdir, basename + ".stdout")
        logging.info(
            f"stdout_file was not specified and therefore was set to '{stdout_file}'"
        )

    if stderr_file is None:
        primary = cmd.split(" ")[0]
        basename = os.path.basename(primary)
        stderr_file = os.path.join(outdir, basename + ".stderr")
        logging.info(
            f"stderr_file was not specified and therefore was set to '{stderr_file}'"
        )

    if os.path.exists(stdout_file):
        logging.info(
            f"STDOUT file '{stdout_file}' already exists so will delete it now"
        )
        os.remove(stdout_file)

    if os.path.exists(stderr_file):
        logging.info(
            f"STDERR file '{stderr_file}' already exists so will delete it now"
        )
        os.remove(stderr_file)

    consolidated_cmd = cmd
    p = subprocess.Popen(consolidated_cmd, shell=True)

    (stdout, stderr) = p.communicate()

    pid = p.pid

    logging.info(f"The child process ID is '{pid}'")
    if verbose:
        print(f"The child process ID is '{pid}'")

    p_status = p.wait()

    p_returncode = p.returncode

    if p_returncode is not None:
        logging.info(f"The return code was '{p_returncode}'")
    else:
        logging.info("There was no return code")

    if p_status == 0:
        logging.info(f"Execution of cmd '{cmd}' has completed")
    else:
        raise Exception(f"Received status '{p_status}'")

    if stdout is not None:
        logging.info("stdout is: " + stdout_file)

    if stderr is not None:
        logging.info("stderr is: " + stderr_file)

    return stdout_file

def validate_verbose(ctx, param, value):
    if value is None:
        click.secho("--verbose was not specified and therefore was set to 'True'", fg='yellow')
        return DEFAULT_VERBOSE
    return value


@click.command()
@click.option("--logfile", help="The log file")
@click.option("--outdir", help=f"The output directory - default is '{DEFAULT_OUTDIR}'")
@click.option(
    "--part",
    type=click.Choice(["major", "minor", "patch"]),
    help="Required: The part that should be bumped i.e.: major or minor or patch",
)
@click.option(
    "--verbose",
    is_flag=True,
    help=f"Will print more info to STDOUT - default is '{DEFAULT_VERBOSE}'",
    callback=validate_verbose
)
def main(logfile: str, outdir: str, part: str, verbose: bool):
    """Helper script for bumping the version of the software."""
    error_ctr = 0

    if part is None:
        error_console.print("--part was not specified")
        error_ctr += 1

    if error_ctr > 0:
        error_console.print("Detected problems with input")
        sys.exit(1)

    if outdir is None:
        outdir = DEFAULT_OUTDIR
        console.print(
            f"[bold yellow]--outdir was not specified and therefore was set to default '{outdir}'[/]"
        )

    assert isinstance(outdir, str)

    if not os.path.exists(outdir):
        pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
        console.print(f"[bold yellow]Created output directory '{outdir}'[/]")

    if logfile is None:
        logfile = os.path.join(outdir, os.path.basename(__file__) + ".log")
        console.print(
            f"[bold yellow]--logfile was not specified and therefore was set to '{logfile}'[/]"
        )

    assert isinstance(logfile, str)

    logging.basicConfig(
        filename=logfile,
        format=LOGGING_FORMAT,
        level=LOG_LEVEL
    )

    if not os.path.exists(DEFAULT_BUMPVERSION_CONFIG_FILE):
        error_console.print(f"File '{DEFAULT_BUMPVERSION_CONFIG_FILE}' does not exist")
        sys.exit(1)

    bakfile = backup_file(DEFAULT_PRE_COMMIT_HOOK_FILE)

    cmd = f"bumpversion {part} --allow-dirty"

    _execute_cmd(cmd, outdir=outdir, verbose=verbose)

    if bakfile is not None:
        if os.path.exists(bakfile):
            restore_file(bakfile)
        else:
            raise Exception(f"File '{bakfile}' does not exist")
    else:
        print("No backup file was created")

    print("Remember to execute 'git push --tags'")

    print(f"The log file is '{logfile}'")
    console.print(f"[bold green]Execution of '{os.path.abspath(__file__)}' completed[/]")
    sys.exit(0)


if __name__ == "__main__":
    main()
