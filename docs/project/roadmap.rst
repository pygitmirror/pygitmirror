Roadmap
=======

The work which is open, most useful first within each part. This page is
the list of record: when an item is done, remove it and add the change to
the :doc:`changelog`; when new work is found or put off, add it here.

Before the web version
----------------------

What the library needs so that a service can be built on it. See
:doc:`design` for what is there already.

* **Try every host with a token.** Creating, changing and archiving were
  tested against stand-ins only; see :doc:`maintenance` for what was
  verified against the real services. This comes first: it is the one part
  of the package which is not known to work.
* **Limits and retries of the APIs.** A request which is refused for rate
  limiting (HTTP 429, or 403 with the headers of GitHub) should wait and
  try again. A run over hundreds of repositories will meet the limits.
* **A lock on the local mirror.** Two operations on the same folder at the
  same time corrupt nothing in git, but one may push what the other
  fetched. A lock file per mirror would make it safe to share a work
  folder between workers.
* **Progress within a repository.** A large repository takes minutes to
  fetch and push. git reports progress on its error stream; passing it to a
  callback would let a page show more than "running".
* **Results as plain data.** ``MirrorResult`` should convert to and from a
  dictionary, to be stored and sent to a browser.
* **Cancelling.** An operation cannot be stopped from outside except by its
  timeout.

The web version
---------------

A web application in which a user connects accounts on GitHub, GitLab,
Gitea and Bitbucket and clones, keeps in sync or migrates repositories
between them. It is a separate program which uses this package. Open
questions, to be decided when it is designed:

* How accounts are connected: OAuth applications on each host, or tokens
  pasted by the user. OAuth tokens expire and must be refreshed.
* Where tokens are stored, and how they are encrypted.
* How syncs are scheduled, and whether webhooks of the source trigger
  them.
* Whether local mirrors are kept between syncs. They save downloads and
  cost disk space, per repository and per user.
* Whether it is run as a service, or installed by each user.

More to copy
------------

* **Git LFS files.** The pointers are copied and the files are not, which
  leaves the destination broken for repositories which use LFS. Needs
  ``git lfs fetch --all`` and ``git lfs push --all``, and the ``git-lfs``
  program.
* **Wikis.** A wiki is a second git repository on every host, at
  ``<name>.wiki.git``, and can be copied in the same way.
* **Topics, the home page and whether issues are enabled.**
* **Issues, pull requests and releases.** Each host has its own model.
  GitHub, GitLab and Gitea have importers for some directions, which may
  be the better tool; decide before building one.

Hosts
-----

* **Bitbucket Data Center**, which has an API of its own.
* **Azure DevOps** and **AWS CodeCommit**, if someone asks.

Project
-------

* **Let the daily tests open an issue when they fail.** A scheduled run
  which fails only shows in the Actions tab.
* **Tests against real servers in CI.** Gitea and GitLab run in
  containers; a job could create, sync and archive against them.
