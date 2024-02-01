import logging
import os
import subprocess


DEFAULT_VERBOSE = False


def execute_cmd(
    cmd: str,
    outdir: str = None,
    stdout_file=None,
    stderr_file=None,
    verbose: bool = DEFAULT_VERBOSE,
) -> str:
    """Execute a command via system call using the subprocess module.

    Args:
        cmd (str): The executable to be invoked.
        outdir (str): The output directory where STDOUT, STDERR and the shell script should be written to.
        stdout_file (str): The file to which STDOUT will be captured in.
        stderr_file (str): The file to which STDERR will be captured in.
    Returns:
        str: The path to the file where STDOUT was written to.
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
        stdout_file = _derive_std_file(cmd, outdir, "stdout")

    if stderr_file is None:
        stderr_file = _derive_std_file(cmd, outdir, "stderr")


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

def _derive_std_file(cmd: str, outdir: str, std_type: str) -> str:
    """Derive the path to the file where STDOUT or STDERR will be written to.

    Args:
        cmd (str): The executable to be invoked.
        outdir (str): The output directory where STDOUT, STDERR and the shell script should be written to.
        std_type (str): The type of output - either stdout or stderr.

    Raises:
        Exception: _description_

    Returns:
        str: _description_
    """
    primary = cmd.split(" ")[0]

    basename = os.path.basename(primary)

    std_file = os.path.join(outdir, f"{basename}.{std_type}")
    logging.info(
        f"stdout_file was not specified and therefore was set to '{stdout_file}'"
    )

    return std_file
