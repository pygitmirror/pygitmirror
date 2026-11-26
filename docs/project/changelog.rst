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

* **A page**: ``git-mirror serve`` serves a page on your own machine which
  runs the operations in a browser, with a preview, results per
  repository, and a readout of the disk space of the local copies. It
  offers Gitea and Forgejo, GitLab, and plain git servers. See
  :doc:`/guide/web`.
* **A Docker image** of the page, built on bare Alpine, with a
  ``compose.yaml``.
* ``Mirror.forget()`` deletes the local mirror of a repository, and
  ``MirrorResult.to_dict()`` and ``MirrorPlan.to_dict()`` give results as
  plain data.

Documentation
~~~~~~~~~~~~~

* New pages: :doc:`ui-design`, :doc:`security` and :doc:`host-notes`, and
  a roadmap in stages.
* Diagrams of how a repository travels, of what each operation does to a
  branch or tag, of the packages and of the steps of an operation.

Versions
--------

.. toctree::
   :maxdepth: 1

   changelog/0.1
   changelog/0.0
