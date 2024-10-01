# Clone Gitea

## Development

To clone the library for development:

    git clone

or

    git clone

### Build The Virtual Environment

The current earliest Python version supported is `3.11`. You need to be able to create a virtual environment at this version to make sure any changes you make is compatible.

If you are using `conda`:

    conda create --prefix=.venv python=3.11 --yes

If you are using `venv`, make sure you have the right base package:

    >> python --version
    Python 3.11.x

Once you verify your base Python, you can then create a virtual environment using:

    virtualenv -p py3.11 .venv

### Setup

Once you have created your virtual environment and made sure it is active in your current command line:

    pip install -e .[dev]

This should all the dependencies you need for developing into the library and also allow you to run the unit tests:

    pytest

### Debugging

WIP
