Changelog
=========

All notable changes to ``pygitmirror``, most recent first, with one page
per minor version.

Changes which are merged and not released yet are listed here, under a
heading "Unreleased". At a release they move to the page of their version.

Unreleased
----------

Added
~~~~~

* **Failures say what to do.** A repository which fails is reported with a
  sentence in plain words, for the common causes: no such repository, a
  token which is refused or lacks permission, an owner which does not
  exist, a protected branch, a full disk, a server which cannot be
  reached. The page shows it, with what the server said behind a click;
  the command logs it; the library has it as ``MirrorResult.advice``.

Fixed
~~~~~

* git is asked to speak English, whatever the language of the user, so
  that its messages can be recognized.

Documentation
~~~~~~~~~~~~~

* Pictures of the page in the README and in :doc:`/guide/web`, and badges
  for downloads and for the Docker image.

Project
~~~~~~~

* The tools which build the documentation need Python 3.12 or newer,
  which removes a vulnerable version of a dependency of the theme from
  the lock file. The package itself still supports Python 3.11.

Versions
--------

.. toctree::
   :maxdepth: 1

   changelog/0.2
   changelog/0.1
   changelog/0.0
