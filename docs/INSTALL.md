# INSTALL

## Install from PYPI

Install the package in your Python virtual environment

```shell
source venv/bin/activate
pip install slurm-workflow-utils
```

## Clone project

You can `git clone` this project.

```shell
git clone https://github.com/jai-python3/slurm-workflow-utils.git
cd slurm-workflow-utils
```

## Local pip install

You can optionally establish a Python virtual environment.
Then you can run the `setup.py` script to build to project and then run `pip install`<br>
to install in your local Python virtual environment.

```shell
virtualenv -p python3 venv
source venv/bin/activate
python setup.py sdist
pip install .
```

## Uninstall

You can uninstall like this:

```bash
source venv/bin/activate
pip uninstall slurm-workflow-utils
make clean
```

## Developers

If you modify the code in this package in your local virtual environment:

```shell
pip uninstall slurm-workflow-utils
make clean
python setup.py sdist
pip install .
```

## Publish to PYPI

You want can publish the code in this package to the PYPI repository.

### Install twine and setuptools

Install `twine` and `setuptools`.

```shell
pip install twine setuptools
```

### Build the Distribution Package

```shell
python setup.py sdist bdist_wheel
```

### Configure your ~/.pypirc:

```bash
[pypi]
  username = __token__
  password = pypi-YOUR-TOKEN
```

### Upload Your Package to PyPI

```shell
twine upload dist/*
```

