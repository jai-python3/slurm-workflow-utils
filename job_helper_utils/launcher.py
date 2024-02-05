import logging
import os

from pathlib import Path
from rich.console import Console
from typing import List, Optional

from . import constants
from .file_utils import check_infile_status


error_console = Console(stderr=True, style="bold red")

console = Console()


class Launcher:
    """Class for launching SLURM sbatch shell scripts."""

    def __init__(self, **kwargs):
        """Constructor for Launcher."""
        self.sbatch_list_file = kwargs.get("sbatch_list_file", None)
        self.logfile = kwargs.get("logfile", None)
        self.outdir = kwargs.get("outdir", None)
        self.verbose = kwargs.get("verbose", constants.DEFAULT_VERBOSE)

        logging.info(f"Instantiated Builder in file '{os.path.abspath(__file__)}'")


    def _get_file_list_from_sbatch_list_file(self) -> List[str]:
        """Read the sbatch list file and return the list of sbatch scripts.

        Returns:
            List[str]: The list of sbatch scripts.
        """
        check_infile_status(self.sbatch_list_file)

        file_list = []

        with open(self.sbatch_list_file, "r") as file:
            line_ctr = 0
            for line in file:
                line_ctr += 1
                if line.startswith("#"):
                    continue
                if line.strip() == "":
                    continue
                file_list.append(line.strip())

        logging.info(f"Read '{line_ctr}' lines from sbatch list file '{self.sbatch_list_file}'")
        return file_list


    def launch_all(self) -> None:
        """Launch all of the sbatch scripts in the sbatch list file."""

        file_list = self._get_file_list_from_sbatch_list_file()

        ctr = 0

        for sbatch_script in file_list:
            ctr += 1

            check_infile_status(sbatch_script)

            if self.verbose:
                console.log(f"Will launch sbatch script {ctr}: '{sbatch_script}'")
            logging.info(f"Will launch sbatch script {ctr}: '{sbatch_script}'")

            # os.system(f"sbatch {sbatch_script}")


        logging.info(f"Launched '{ctr}' sbatch scripts from sbatch list file '{self.sbatch_list_file}'")
