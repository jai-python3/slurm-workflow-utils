"""
A collection of utility functions for file management and data integrity.

Functions:
- calculate_md5(file_path): Calculate the MD5 hash of a file specified by its path.
- check_indir_status(indir=None): Check the status of a directory, providing information on its existence and contents.
- check_infile_status(infile, extension=None): Check the status of a file, including its existence and optionally validate its extension.
- get_file_creation_date(file_path): Retrieve the creation date of a file specified by its path.
- get_file_list(indir=None, extension=None): Get the list of files in the specified directory.
- get_file_size(file_path): Get the size of a file specified by its path.
- get_line_count(file_path): Get the number of lines in a file specified by its path.
- is_binary_file(file_path, block_size=1024): Determine whether a file is binary or text.

Use these functions to enhance file handling and data validation in your Python projects.
"""


import hashlib
import logging
import os
import platform
import sys
import string

from typing import List, Optional
from rich.console import Console
from datetime import datetime

error_console = Console(stderr=True, style="bold red")


def calculate_md5(file_path: str) -> str:
    """Calculate the md5 checksum for the specified file.

    Args:
        file_path (str): the file for which the md5 checksum will be calculated

    Returns:
        str: the calculated md5 checksum
    """
    md5_hash = hashlib.md5()
    logging.info(f"Will attempt to calculate the MD5 checksum for file '{file_path}'")

    with open(file_path, "rb") as file:
        # Read the file in chunks to efficiently handle large files
        for chunk in iter(lambda: file.read(4096), b""):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


def get_file_creation_date(file_path: str) -> datetime:
    """Determine the creation date for the specified file.

    Args:
        file_path (str): the absolute path of the file

    Returns:
        datetime: the date the file was created according to the operating system
    """
    if platform.system() == "Windows":
        # On Windows, use creation time
        creation_time = os.path.getctime(file_path)
    else:
        # On Unix-based systems, use birth time (creation time)
        # Note: Not all file systems support birth time, and it might not be available on some systems.
        stat_info = os.stat(file_path)
        creation_time = stat_info.st_mtime

    # Convert the timestamp to a readable date
    creation_date = datetime.fromtimestamp(creation_time)

    return creation_date


def check_infile_status(infile: str, extension: Optional[str] = None) -> None:
    """Check if the file exists, if it is a regular file and whether it has
    content.

    Args:
        infile (str): the file to be checked

    Raises:
        None
    """

    error_ctr = 0

    if infile is None or infile == "":
        error_console.print(f"'{infile}' is not defined")
        error_ctr += 1
    else:
        if not os.path.exists(infile):
            error_ctr += 1
            error_console.print(f"'{infile}' does not exist")
        else:
            if not os.path.isfile(infile):
                error_ctr += 1
                error_console.print(f"'{infile}' is not a regular file")
            if os.stat(infile).st_size == 0:
                error_console.print(f"'{infile}' has no content")
                error_ctr += 1
            if extension is not None and not infile.endswith(extension):
                error_console.print(
                    f"'{infile}' does not have filename extension '{extension}'"
                )
                error_ctr += 1

    if error_ctr > 0:
        error_console.print(f"Detected problems with input file '{infile}'")
        sys.exit(1)


def check_indir_status(indir: str = None) -> None:
    """Check if the directory exists and is a regular directory.

    Args:
        indir (str): the directory to be checked
    """
    error_ctr = 0

    if indir is None or indir == '':
        error_console.print(f"'{indir}' is not defined")
        error_ctr += 1
    else:
        if not os.path.exists(indir):
            error_ctr += 1
            error_console.print(f"directory '{indir}' does not exist")
        else:
            if not os.path.isdir(indir):
                error_ctr += 1
                error_console.print(f"'{indir}' is not a regular directory")

    if error_ctr > 0:
        error_console.print(f"Detected problems with input directory '{indir}'")
        sys.exit(1)


def get_file_size(file_path: str) -> int:
    # Check if the file exists
    if os.path.exists(file_path):
        # Get the file size in bytes
        file_size = os.path.getsize(file_path)
        return file_size
    else:
        raise Exception(f"The file '{file_path}' does not exist.")


def get_line_count(file_path: str) -> int:
    # if is_binary_file(file_path):
    #     print(f"Unable to get line count for binary file '{file_path}'")
    #     return None
    try:
        with open(file_path, 'r') as file:
            line_count = sum(1 for line in file)
        return line_count
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def is_binary_file(file_path: str, block_size: int = 1024) -> bool:
    try:
        with open(file_path, 'rb') as file:
            block = file.read(block_size)
            if not block:  # Empty file
                return False

            # Check for the presence of null bytes (indicative of binary files)
            if b'\x00' in block:
                return True

            # Check for a significant number of non-printable ASCII characters
            text_characters = set(string.printable)
            if not all(byte in text_characters or byte == b'\n' for byte in block):
                return True

            return False  # File is likely text

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_file_list(indir: str = None, extension: str = None) -> List[str]:
    """Get the list of files in the specified directory.

    Args:
        indir (str): the directory to search for files
        extension (str): the file extension to filter on

    Returns:
        file_list (List[str]): the list of files found in the directory
    """
    if extension is None:
        logging.info(f"Going to search for files in directory '{indir}'")
    else:
        logging.info(f"Going to search for files with extension '{extension}' in directory '{indir}'")

    file_list = []

    for dirpath, dirnames, filenames in os.walk(indir):

        if 'venv' in dirpath:
            logging.info(f"Going to ignore files in directory '{dirpath}'")
            continue
        for name in filenames:
            filepath = os.path.normpath(os.path.join(dirpath, name))
            if os.path.isfile(filepath):
                if extension is not None:
                    if filepath.endswith(f'.{extension}'):
                        file_list.append(filepath)
                else:
                    file_list.append(filepath)

    return file_list

