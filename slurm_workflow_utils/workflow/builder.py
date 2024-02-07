import logging
import os
import yaml

from pathlib import Path
from rich.console import Console
from typing import Any, Dict, List, Optional
from simple_template_toolkit import STTManager as TemplateToolkitManager

from .. import constants
from ..file_utils import check_infile_status


error_console = Console(stderr=True, style="bold red")

console = Console()


class Maker:
    """Class for build all of the SLURM shell scripts to orchestrate a workflow."""

    def __init__(self, **kwargs):
        """Constructor for Maker."""
        self.control_file = kwargs.get("control_file", None)
        self.logfile = kwargs.get("logfile", None)
        self.outdir = kwargs.get("outdir", None)
        self.verbose = kwargs.get("verbose", constants.DEFAULT_VERBOSE)

        logging.info(f"Will load contents of config file 'infile'")
        self.control_lookup = yaml.safe_load(Path(self.control_file).read_text())

        logging.info(f"Instantiated Maker in file '{os.path.abspath(__file__)}'")

    def build(self) -> None:
        if "job_sets" not in self.control_lookup:
            raise ValueError(f"'job_sets' was not found in control file '{self.control_file}'")
        job_sets_lookup = self.control_lookup["job_sets"]

        if "workflow" not in self.control_lookup:
            raise ValueError(f"'workflow' was not found in control file '{self.control_file}'")

        if "common" not in self.control_lookup["workflow"]:
            raise ValueError(f"'common' was not found in control file '{self.control_file}'")
        common_lookup = self.control_lookup["workflow"]["common"]

        if "%KEY%" not in common_lookup:
            raise ValueError(f"'%KEY%' was not found in common_lookup '{common_lookup}'")
        key_placeholder = common_lookup["%KEY%"]

        if "definitions" not in self.control_lookup["workflow"]:
            raise ValueError(f"'definitions' was not found in control file '{self.control_file}'")
        definitions_lookup = self.control_lookup["workflow"]["definitions"]

        template_file = None
        if "template_file" in self.control_lookup["workflow"]:
            template_file = self.control_lookup["workflow"]["template_file"]

        if common_lookup["%TIMESTAMP%"] is None or common_lookup["%TIMESTAMP%"] == "":
            common_lookup["%TIMESTAMP%"] = constants.DEFAULT_TIMESTAMP
            logging.info(f"%TIMESTAMP% was not specified and therefore was set to '{constants.DEFAULT_TIMESTAMP}'")

        for job_set in job_sets_lookup:
            if key_placeholder not in job_set:
                raise ValueError(f"key_placeholder '{key_placeholder}' was not found in job_set '{job_set}'")
            key = job_set[key_placeholder]

            job_lookup = job_set
            job_lookup.update(common_lookup)
            for job_definition in definitions_lookup:
                if "template_file" not in job_definition or job_definition["template_file"] is None or job_definition == "":
                    if template_file is None:
                        raise ValueError(f"job_definition['template_file'] was not defined for job with name '{job_definition['%JOB_NAME%']}'")
                    job_definition["template_file"] = template_file
                    logging.info(f"job_definition['template_file'] was not defined and therefore was set to common template file '{template_file}'")
                job_lookup.update(job_definition)

            job_file = self._write_job_lookup_to_file(job_lookup)

            manager = TemplateToolkitManager(
                verbose=self.verbose
            )

            outfile = os.path.join(
                self.outdir,
                f"{key}.sbatch.sh"
            )

            job_file = self._write_job_lookup_to_file(job_lookup, key)

            manager.make_substitutions(
                key_val_file=job_file,
                template_file=template_file,
                outfile=outfile,
            )

    def _write_job_lookup_to_file(self, job_lookup: Dict[str, Any], key: str) -> str:
        """Write the job lookup to a file.

        Args:
            job_lookup (Dict[str, Any]): The job lookup.
            key (str): The key.
        Returns:
            str: The job file.
        """
        job_file = os.path.join(self.outdir, f"{key}.yaml")
        with open(job_file, "w") as file:
            yaml.dump(job_lookup, file)

        return job_file


