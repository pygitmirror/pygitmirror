pygitmirror
===========

|tests| |docs| |pypi| |pyversions| |license|

.. |tests| image:: https://github.com/pygitmirror/pygitmirror/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/pygitmirror/pygitmirror/actions/workflows/tests.yml
    :alt: Tests

.. |docs| image:: https://readthedocs.org/projects/pygitmirror/badge/?version=latest
    :target: https://pygitmirror.readthedocs.io/
    :alt: Documentation

.. |pypi| image:: https://img.shields.io/pypi/v/pygitmirror
    :target: https://pypi.org/project/pygitmirror/
    :alt: PyPI version

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/pygitmirror
    :target: https://pypi.org/project/pygitmirror/
    :alt: Python versions

.. |license| image:: https://img.shields.io/pypi/l/pygitmirror
    :target: https://github.com/pygitmirror/pygitmirror/blob/master/LICENSE
    :alt: License

``pygitmirror`` copies git repositories from one host to another: GitHub,
GitLab, Gitea, Bitbucket, or any git server. It is a command, ``git-mirror``,
and a Python library with the same abilities.

.. code-block:: bash

   export GIT_MIRROR_SOURCE_TOKEN=...       # a GitHub token
   export GIT_MIRROR_DESTINATION_TOKEN=...  # a Gitea token

   git-mirror sync --source github \
       --destination gitea --destination-url https://git.example.com \
       --org my-org --all

.. image:: /_static/overview-light.svg
   :class: only-light
   :width: 100%
   :alt: The source is fetched into a local mirror, which is pushed to the destination; the APIs of the two hosts read and create the repositories

.. image:: /_static/overview-dark.svg
   :class: only-dark
   :width: 100%
   :alt: The source is fetched into a local mirror, which is pushed to the destination; the APIs of the two hosts read and create the repositories

It does three things, which differ in what they may change at the
destination:

* **clone** copies the branches and tags which the destination does not
  have, and never overwrites or deletes anything there
* **sync** makes the destination equal to the source, run after run
* **migrate** clones, checks that the copy is complete, and can archive the
  source

All three create the destination repository when it is missing, with the
description and the visibility of the source. See :doc:`guide/operations`.

The package has no dependencies: it runs the ``git`` executable and uses the
standard library for the APIs of the hosts. Tokens are read from the
environment and are never written to a file, a URL or a command line.

``pygitmirror`` is maintained by `Bassem Girgis <https://girgis.me>`_.

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   getting-started/installation
   getting-started/quickstart

.. toctree::
   :maxdepth: 2
   :caption: User guide

   guide/operations
   guide/hosts
   guide/command-line
   guide/library

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/index

.. toctree::
   :maxdepth: 2
   :caption: Project

   project/design
   project/decisions
   project/roadmap
   project/changelog
   project/development
   project/maintenance
   project/license

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
