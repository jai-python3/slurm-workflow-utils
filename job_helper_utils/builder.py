import logging
import os
import pathlib
import sys
import yaml

from datetime import datetime
from yamlordereddictloader import SafeLoader
from pathlib import Path
from rich.console import Console
from typing import Any, Dict, List, Optional
from simple_template_toolkit import STTManager as TemplateToolkitManager

from . import constants
from .file_utils import check_infile_status


error_console = Console(stderr=True, style="bold red")

console = Console()


class Builder:
    """Class for build all of the SLURM shell scripts to orchestrate a workflow."""

    def __init__(self, **kwargs):
        """Constructor for Builder."""
        self.control_file = kwargs.get("control_file", None)
        self.logfile = kwargs.get("logfile", None)
        self.outdir = kwargs.get("outdir", None)
        self.verbose = kwargs.get("verbose", constants.DEFAULT_VERBOSE)

        logging.info(f"Will load contents of config file '{self.control_file}'")
        # self.control_lookup = yaml.safe_load(Path(self.control_file).read_text())
        with open(self.control_file, "r") as file:
            self.control_lookup = yaml.load(file, Loader=SafeLoader)

        logging.info(f"Instantiated Builder in file '{os.path.abspath(__file__)}'")

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
        if "template_file" in self.control_lookup["workflow"]["common"]:
            template_file = self.control_lookup["workflow"]["common"]["template_file"]
        else:
            logging.info(f"template_file was not defined in the [workflow][common] section of the control file '{self.control_file}'")

        if common_lookup["%TIMESTAMP%"] is None or common_lookup["%TIMESTAMP%"] == "":
            common_lookup["%TIMESTAMP%"] = constants.DEFAULT_TIMESTAMP
            logging.info(f"%TIMESTAMP% was not specified and therefore was set to '{constants.DEFAULT_TIMESTAMP}'")

        sbatch_script_list = []

        # Process each job set.
        for subflow_ctr, job_set in enumerate(job_sets_lookup, start=1):
            logging.info(f"job_set: {job_set}")

            if key_placeholder not in job_set:
                raise ValueError(f"key_placeholder '{key_placeholder}' was not found in job_set '{job_set}'")
            key = job_set[key_placeholder]

            job_lookup = job_set
            job_lookup.update(common_lookup)

            previous_job_name = None

            subflow_symlink_name = self._create_subflow_directory(f"{common_lookup['%JOB_SET_OUTDIR%']}/{common_lookup['%TIMESTAMP%']}/{key}", subflow_ctr)

            # Process each job definition.
            for job_ctr, job_definition in enumerate(definitions_lookup, start=1):
                step_number = f"step-{job_ctr}"
                logging.info(f"Processing step '{step_number}' job_definition: {job_definition}")

                if "template_file" not in job_definition or job_definition["template_file"] is None or job_definition == "":
                    if template_file is None:
                        raise ValueError(f"job_definition['template_file'] was not defined for job with name '{job_definition['%JOB_NAME%']}'")
                    job_definition["template_file"] = template_file
                    logging.info(f"job_definition['template_file'] was not defined and therefore was set to common template file '{template_file}'")

                if job_ctr == 1:
                    job_definition["%DEPENDENCY%"] = ""
                else:
                    if previous_job_name is None or previous_job_name == "":
                        raise ValueError(f"previous_job_name was not defined while processing job with name '{job_definition['%JOB_NAME%']}'")

                    job_definition["%DEPENDENCY%"] = f"#SBATCH --dependency=afterok:{previous_job_name}"

                if "%STDOUT%" not in job_definition:
                    job_definition["%STDOUT%"] = f"{common_lookup['%JOB_SET_OUTDIR%']}/{common_lookup['%TIMESTAMP%']}/{key}/{job_definition['%JOB_NAME%']}/{job_definition['%JOB_NAME%']}.stdout"

                if "%STDERR%" not in job_definition:
                    job_definition["%STDERR%"] = f"{common_lookup['%JOB_SET_OUTDIR%']}/{common_lookup['%TIMESTAMP%']}/{key}/{job_definition['%JOB_NAME%']}/{job_definition['%JOB_NAME%']}.stderr"

                job_lookup.update(job_definition)
                # print(f"{job_lookup=}")
                # sys.exit(1)

                self._perform_inplace_substitutions(job_lookup)

                job_file = os.path.join(
                    # self.outdir,
                    common_lookup['%JOB_SET_OUTDIR%'],
                    common_lookup['%TIMESTAMP%'],
                    key,
                    job_lookup['%JOB_NAME%'],
                    f"{job_lookup['%JOB_NAME%']}.yaml"
                )

                job_symlink_name = self._create_job_directory(job_file, job_ctr)

                logging.info(f"{job_file=}")
                logging.info(f"{job_lookup=}")
                # sys.exit(1)


                self._write_job_lookup_to_file(job_lookup, job_file)

                outfile = os.path.join(
                    # self.outdir,
                    common_lookup['%JOB_SET_OUTDIR%'],
                    common_lookup['%TIMESTAMP%'],
                    key,
                    job_lookup['%JOB_NAME%'],
                    f"{job_lookup['%JOB_NAME%']}.sbatch.sh"
                )


                self._write_job_lookup_to_file(job_lookup, job_file)
                logging.info(f"{job_file=} {template_file=} {outfile=}")

                manager = TemplateToolkitManager(
                    verbose=self.verbose
                )

                manager.make_substitutions(#job_file, template_file, outfile)
                    key_val_file=job_file,
                    template_file=template_file,
                    outfile=outfile,
                )

                sbatch_script_list.append(outfile)

                previous_job_name = job_lookup["%JOB_NAME%"]
                logging.info(f"Set previous_job_name to '{previous_job_name}'")

        self._write_sbatch_script_list_to_file(
            sbatch_script_list,
            f"{common_lookup['%JOB_SET_OUTDIR%']}/{common_lookup['%TIMESTAMP%']}"
        )

    def _write_sbatch_script_list_to_file(self, sbatch_script_list: List[str], outdir: str) -> None:
        """Write the sbatch script list to a file.

        Args:
            sbatch_script_list (List[str]): The sbatch script list.
            outdir (str): The output directory.
        """
        outfile = os.path.join(outdir, "sbatch_scripts.txt")
        with open(outfile, "w") as of:
            of.write(f"## method-created: {os.path.abspath(__file__)}\n")
            of.write(f"## date-created: {str(datetime.today().strftime('%Y-%m-%d-%H%M%S'))}\n")
            of.write(f"## created-by: {os.environ.get('USER')}\n")
            of.write(f"## control-file: {self.control_file}\n")
            of.write(f"## logfile: {self.logfile}\n")

            for sbatch_script in sbatch_script_list:
                of.write(f"{sbatch_script}\n")

        if self.verbose:
            console.log(f"Wrote sbatch script list to file '{outfile}'")
        logging.info(f"Wrote sbatch script list to file '{outfile}'")

    def _perform_inplace_substitutions(self, lookup: Dict[str, Any]) -> None:
        """Perform the placeholder substitutions among the values in the job definition lookup.

        Args:
            lookup (Dict[str, Any]): The job definition lookup.
        """
        for _ in range(3):
            for key in lookup:
                for current_key, val in lookup.items():
                    if key == current_key:
                        continue
                    # print(f"{key=} {current_key=} {val=}")
                    if key in val:
                        lookup[current_key] = val.replace(key, lookup[key])


    def _write_job_lookup_to_file(self, job_lookup: Dict[str, Any], job_file: str) -> None:
        """Write the job lookup to a file.

        Args:
            job_file (str): The output job file.
            job_lookup (Dict[str, Any]): The job lookup.
        """
        dirname = os.path.dirname(job_file)
        if not os.path.exists(dirname):
            pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory '{dirname}'")

        with open(job_file, "w") as file:
            yaml.dump(dict(job_lookup), file)


    def _create_job_directory(self, job_file: str, job_ctr: int) -> str:
        """Create the job directory and symlink to the job directory.

        Args:
            job_file (str): The job file.
            job_ctr (int): The job counter.
        Returns:
            str: The symlink to the job directory.
        """

        # E.g.: job_file:
        # /tmp/workflow-1/2024-02-05-092539/sample-5/rsync-R000989_NML05959-sample-5/rsync-R000989_NML05959-sample-5.sbatch.sh
        job_dir = os.path.dirname(job_file)

        # E.g.: job_dir:
        # /tmp/workflow-1/2024-02-05-092539/sample-5/rsync-R000989_NML05959-sample-5
        if not os.path.exists(job_dir):
            pathlib.Path(job_dir).mkdir(parents=True, exist_ok=True)
            logging.info(f"Created directory '{job_dir}'")

        current_dir = os.getcwd()

        # Create a step symlink to the job directory.
        parent_dir = os.path.dirname(job_dir)
        # E.g.: parent_dir:
        # /tmp/workflow-1/2024-02-05-092539/sample-5

        os.chdir(parent_dir)

        job_basedir = os.path.basename(job_dir)
        # E.g.: job_basedir:
        # rsync-R000989_NML05959-sample-5

        symlink = f"step-{job_ctr}"
        # E.g.: symlink:
        # step-1

        # Create symlink to the job directory.
        if not os.path.exists(symlink):
            os.symlink(job_basedir, symlink)
            # E.g.: step-1 -> rsync-R000989_NML05959-sample-5
            logging.info(f"Created symlink '{symlink}'")

        # Return to the original directory.
        os.chdir(current_dir)

        return symlink


    def _create_subflow_directory(self, subflow_dir: str, subflow_ctr: int) -> str:
        """Create the subflow directory and symlink to the subflow directory.

        Args:
            subflow_dir (str): The subflow directory.
            subflow_ctr (int): The subflow counter.
        Returns:
            str: The symlink to the subflow directory.
        """

        # E.g.: subflow_dir:
        # /tmp/workflow-1/2024-02-05-092539/sample-5
        if not os.path.exists(subflow_dir):
            pathlib.Path(subflow_dir).mkdir(parents=True, exist_ok=True)
            logging.info(f"Created subflow directory '{subflow_dir}'")

        current_dir = os.getcwd()

        # Create a step symlink to the subflow directory.
        parent_dir = os.path.dirname(subflow_dir)
        # E.g.: parent_dir:
        # /tmp/workflow-1/2024-02-05-092539

        os.chdir(parent_dir)

        subflow_basedir = os.path.basename(subflow_dir)
        # E.g.: subflow_basedir:
        # sample-5

        symlink = f"subflow-{subflow_ctr}"
        # E.g.: symlink:
        # subflow-5

        # Create symlink to the job directory.
        if not os.path.exists(symlink):
            os.symlink(subflow_basedir, symlink)
            # E.g.: subflow-5 -> sample-5
            logging.info(f"Created symlink '{symlink}'")

        # Return to the original directory.
        os.chdir(current_dir)

        return symlink
