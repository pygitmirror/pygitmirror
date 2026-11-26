Design
======

How the package is built, and why it is built that way. Read it before
changing the structure; the reasons for single choices are in
:doc:`decisions`.

The problem
-----------

Copying a repository from one host to another has two halves which have
nothing in common.

* **The git data** moves through git. Every host speaks the same protocol,
  so this half is the same for all of them.
* **The repository itself**, its existence, its description, visibility and
  default branch, is managed through the API of the host. Every host has
  its own, so this half is different for each.

The package keeps the two apart. One part knows git and no host, one part
knows the hosts and no git, and a third combines them into the operations.

.. code-block:: text

   cli  ──►  config ──►  mirror  ──►  hosts   (where a repository is, and its API)
                            │
                            └─────►  git     (the git executable, a local mirror)

Dependencies go one way, as the arrows point. ``hosts`` and ``git`` do not
import each other, and neither imports ``mirror``.

The layers
----------

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Package
     - Responsibility
   * - ``pygitmirror.git``
     - Runs the git executable. ``Git`` runs one command, never
       interactively. ``LocalMirror`` is a bare repository which is made
       equal to a source by a fetch and pushed to a destination. Functions
       read the branches, tags and default branch of a repository on a
       server.
   * - ``pygitmirror.hosts``
     - One class per service, derived from ``Host``. A host answers where
       the git data of a repository is and how git authenticates there, and
       it reads, creates, lists and changes repositories through the API.
       ``ApiClient`` sends the requests.
   * - ``pygitmirror.mirror``
     - The operations. ``Mirror`` is the entry point of the library;
       ``MirrorPlan`` is the difference between two repositories and
       ``MirrorResult`` what an operation did.
   * - ``pygitmirror.config``
     - Turns a settings file and command line options into ``Settings``.
   * - ``pygitmirror.cli``
     - The ``git-mirror`` command: parses, runs, reports, sets the exit
       status.

The library is ``git``, ``hosts`` and ``mirror``. ``config`` and ``cli``
are one user of it; the web version will be another, and needs neither.

How an operation runs
---------------------

All three operations are one sequence of steps, in
``pygitmirror.mirror._transfer``, with three switches: whether to overwrite,
whether to delete, and whether to verify and archive.

1. **List the source.** ``git ls-remote`` gives the branches and tags of
   the source and what they point to. This also proves that the source
   exists and can be read, before anything is created.
2. **Ensure the destination exists.** With an API: ask for the repository,
   and create it if it is missing, with the description and visibility
   which the API of the source reports. Without an API the next step fails
   if it is missing.
3. **List the destination**, in the same way.
4. **Plan.** ``MirrorPlan.compare`` sorts the references into those to
   create, to update and to delete. If the operation has nothing to change,
   it ends here. This is what makes a frequent sync cheap: two listings and
   no download.
5. **Fetch** the source into the local mirror, and plan again from what was
   fetched, since the source may have moved in the meantime.
6. **Check**, for a clone and a migration: every reference to update must
   be a branch which the source merely moved forward. Anything else is
   reported as diverged, before the push.
7. **Push** the local mirror to the destination, with force for a sync.
8. **Set the default branch** of the destination to that of the source.
9. **Delete**, for a sync, what the source does not have. This is a second
   push, after step 8, because a host refuses to delete its default branch:
   when the source renamed its default branch, the new one has to be the
   default before the old one can go.
10. **Verify**, for a migration: list the destination again and compare it
    with what was fetched.
11. **Archive the source**, for a migration which asked for it.

A dry run stops before every step which changes a host.

The steps are ordered so that an operation which fails leaves both hosts
usable, and can be run again: nothing is deleted before everything was
added, and the source is archived only after the copy was verified.

The local mirror
----------------

Data does not go from host to host directly; git has no such command. It
passes through a bare repository on the machine which runs the operation.

* It holds branches and tags only, fetched with the refspecs
  ``+refs/heads/*:refs/heads/*`` and ``+refs/tags/*:refs/tags/*`` and with
  pruning. After a fetch it is therefore *equal* to the source, and pushing
  all of it is the same as copying the source. No list of references has to
  be passed to git, which matters for repositories with thousands of tags.
* It has no remotes. Each fetch and push names its URL, so the mirror
  stores no address and no credential, and can be deleted or moved at any
  time. It is a cache: losing it costs one full download.
* It is at ``<workdir>/<owner>/<name>.git``, named after the source.

Credentials
-----------

A token must not leak, and it has many ways to: a URL of the form
``https://token@host`` ends up in the configuration of the repository, in
error messages and in the list of processes.

The package therefore never builds such a URL. A host turns its token into
an HTTP ``Authorization`` header, limited to its own address, and hands it
to git as configuration *in the environment* of the one command
(``GIT_CONFIG_COUNT``, ``GIT_CONFIG_KEY_n``, ``GIT_CONFIG_VALUE_n``). The
token is thus in memory and in the environment of a child process, and
nowhere else.

Further rules, each enforced in one place:

* The API client talks to one server. It follows a redirect or a link to a
  next page only on that server, since the standard library would send the
  token along.
* What is logged or put into an error passes through ``redact()``, which
  hides credentials in URLs a user may have written themselves.
* The command takes tokens from the environment only. The library takes
  them as arguments, and never reads the environment itself.
* The representation of a host does not show its token.

Safety against bad input
------------------------

Names and addresses will come from users of a web page. Two places guard
against that:

* ``RepositoryRef`` accepts letters, digits and ``_ . ~ -`` only, no ``..``
  and no leading hyphen. A name can thus neither leave the folder of the
  local mirrors nor be read by git as an option.
* ``Git`` sets ``GIT_ALLOW_PROTOCOL``, so that an address cannot use the
  ``ext`` transport, which runs a command. A service restricts it further
  to ``https`` and ``ssh``, which excludes local folders.

git never asks: ``GIT_TERMINAL_PROMPT=0``, no standard input, and SSH in
batch mode. An operation which lacks a credential fails.

Adding a host
-------------

A host is one module in ``pygitmirror/hosts`` with one class:

1. Derive from ``Host``, or from ``GitHubStyleHost`` when the API follows
   that of GitHub. Set ``provider``, and ``default_url`` if the service has
   a public server.
2. Set ``git_username`` to the user name the service expects with a token
   for git over HTTPS.
3. Implement ``_api_url`` and, if the token is not sent as a bearer token,
   ``_api_headers``.
4. Implement ``get_repository``, ``create_repository``,
   ``list_repositories``, ``set_default_branch`` and
   ``archive_repository``. Set ``can_archive`` to ``False`` and raise
   ``UnsupportedError`` if the service cannot archive.
5. Add the class to ``PROVIDERS`` in ``_factory.py`` and export it.

Nothing else changes: the operations and the command find the host by its
provider name.

What the web version builds on
------------------------------

The web version is a program which calls the library for its users. The
library was shaped for it:

* **An operation is a function call with a result.** ``MirrorResult`` says
  what was created, updated and deleted; errors are exceptions of one
  family. Nothing has to be read from a log.
* **A preview exists.** ``dry_run`` returns the same result without
  changing anything, which a page can show before the user confirms.
* **Many repositories report one by one.** ``Mirror.run`` yields each
  result when it is ready, which is what a progress display needs.
* **Nothing is global.** Hosts and mirrors are objects; tokens are
  arguments. One process can work for many accounts at once.
* **Keeping in sync is repeating a cheap call.** A scheduler calls
  ``sync`` again; an unchanged repository costs two listings.

What it still needs, and the library does not have yet, is listed in the
:doc:`roadmap`.
