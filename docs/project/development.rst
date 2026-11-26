Development
===========

``pygitmirror`` is developed on
`GitHub <https://github.com/pygitmirror/pygitmirror>`_. Bug reports, feature
requests and pull requests are welcome, in particular for further hosts.

Setting up
----------

The project is managed with `uv <https://docs.astral.sh/uv/>`_, and the
common tasks are ``make`` targets. git 2.31 or newer is needed to run the
tests.

.. code-block:: bash

   git clone https://github.com/pygitmirror/pygitmirror.git
   cd pygitmirror
   make install

``make install`` creates a virtual environment in ``.venv`` with the package
and all development tools, exactly as pinned in ``uv.lock``.

Make targets
------------

Run ``make`` without arguments to list the targets.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Target
     - Description
   * - ``make install``
     - create the virtual environment and install all dependencies
   * - ``make install-test``
     - install the package with what the tests need only
   * - ``make install-latest``
     - install what the tests need in its newest versions, ignoring
       ``uv.lock``
   * - ``make lint``
     - check the code style and formatting with ``ruff``
   * - ``make format``
     - format the code and apply the safe lint fixes
   * - ``make typecheck``
     - check the types with ``mypy``
   * - ``make test``
     - run the tests
   * - ``make coverage``
     - run the tests in parallel with a coverage report
   * - ``make check``
     - run every check that CI runs
   * - ``make docs``
     - build this documentation, treating warnings as errors
   * - ``make docs-live``
     - serve the documentation and rebuild it on changes
   * - ``make docs-images``
     - regenerate the diagrams shown in the documentation
   * - ``make version``
     - show the version derived from the git tags
   * - ``make build``
     - build the source distribution and the wheel
   * - ``make check-release TAG=v1.2.3``
     - check that the built distributions have the version of a tag
   * - ``make publish``
     - upload the built distributions to PyPI
   * - ``make clean``
     - remove build, test and cache artifacts

Layout
------

.. code-block:: text

   src/pygitmirror/
       git/        running git, the local mirror
       hosts/      one class per service, and the API client
       mirror/     the operations, their plan and result
       config/     settings from a file and from options
       cli/        the git-mirror command
       errors.py   the exceptions
   tests/          the same layout, and helpers.py
   docs/           this documentation; scripts/ draws its diagrams

:doc:`design` explains how the parts work together and how to add a host.

Code style
----------

* American English in code, comments, documentation and commit messages.
* One public class per module, named after it in snake case. Modules of
  helper functions start with an underscore.
* Files stay under 300 lines; a test checks it for the package.
* ``ruff`` for lint and format, ``mypy`` in strict mode.
* Every public module, class, method and function has a docstring with
  Sphinx field lists (``:param name:``, ``:returns:``, ``:raises Error:``).
  Types are in the hints, not in the docstrings.
* An overriding method is marked with ``override`` from
  ``pygitmirror._compat`` and inherits its docstring.

Tests
-----

The tests need no network and no account.

* **git is real.** Tests of ``git`` and ``mirror`` create repositories in
  a temporary folder and run the git executable on them; ``Workshop`` in
  ``tests/helpers.py`` makes a source with commits. Do not replace git
  with a stand-in: what git does is what is being tested.
* **The APIs are stand-ins.** ``FakeTransport`` answers the requests of a
  host from a table and records them. ``FolderHost`` is a host with an API
  whose repositories are folders, for testing the operations which create
  and archive.

A change to a host should be tried against the real service as well; say
in the pull request what was tried. :doc:`maintenance` has a script for it.

Versions and releases
---------------------

The version is not written in any file. It is read from the git tag when
the package is built: the tag ``v0.2.0`` gives the version ``0.2.0``.

To release:

1. In a pull request, move the "Unreleased" section of the changelog to the
   page of its minor version in ``docs/project/changelog/``, under a
   heading with the version and its date.
2. After it is merged, create a GitHub release on ``master`` with the tag
   ``vX.Y.Z``.

Publishing the release runs the ``Publish`` workflow, which builds the
distributions, checks that their version is that of the tag, and uploads
them to PyPI through trusted publishing.

Continuous integration
----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Workflow
     - What it does
   * - ``Tests``
     - runs the tests on Linux, macOS and Windows with Python 3.11 to 3.14,
       on every pull request and daily; the daily run also tests with the
       newest versions of the tools
   * - ``Quality``
     - runs ``ruff`` and ``mypy`` and builds the documentation
   * - ``CodeQL``
     - scans the Python code and the workflows for vulnerabilities
   * - ``Publish``
     - uploads a release to PyPI

The workflows call make targets only, so that what CI runs can be run
locally in the same way.
