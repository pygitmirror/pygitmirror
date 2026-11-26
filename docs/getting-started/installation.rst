Installation
============

Requirements
------------

* Python 3.11 or newer
* ``git`` 2.31 or newer, on the ``PATH``

``pygitmirror`` has no Python dependencies. It is tested on Python 3.11,
3.12, 3.13 and 3.14 on Linux, macOS and Windows.

Installing from PyPI
--------------------

.. code-block:: bash

   pip install pygitmirror

To install the ``git-mirror`` command for use from anywhere, without adding
the package to a project:

.. code-block:: bash

   uv tool install pygitmirror   # or: pipx install pygitmirror

Installing from GitHub
----------------------

To use changes which are not released yet:

.. code-block:: bash

   pip install git+https://github.com/pygitmirror/pygitmirror.git

Checking the installation
-------------------------

.. code-block:: bash

   git-mirror --version

Installing for development
--------------------------

To work on ``pygitmirror`` itself, see :doc:`/project/development`.
