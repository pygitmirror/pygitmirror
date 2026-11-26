Python Library
==============

Everything the command does is available from Python.

.. code-block:: python

   from pygitmirror import Mirror, make_host

   source = make_host("github", token=github_token)
   destination = make_host("gitea", url="https://git.example.com", token=gitea_token)

   mirror = Mirror(source, destination, workdir="/var/lib/git-mirror")
   result = mirror.sync("my-org/api")
   print(result.summary())

Hosts
-----

:func:`~pygitmirror.hosts.make_host` creates a host from the name of its
provider. The classes can be used directly as well:
:class:`~pygitmirror.hosts.github_host.GitHubHost`,
:class:`~pygitmirror.hosts.gitlab_host.GitLabHost`,
:class:`~pygitmirror.hosts.gitea_host.GiteaHost`,
:class:`~pygitmirror.hosts.bitbucket_host.BitbucketHost` and
:class:`~pygitmirror.hosts.plain_host.PlainHost`.

Unlike the command, the library takes the token as an argument: where it
comes from is the caller's decision. A host keeps it in memory only.

A host can be used on its own to look at repositories:

.. code-block:: python

   from pygitmirror import RepositoryRef

   for info in source.list_repositories("my-org"):
       print(info.ref, info.default_branch, "private" if info.private else "public")

   source.get_repository(RepositoryRef("my-org", "api"))  # None if it does not exist

Operations
----------

:class:`~pygitmirror.mirror.mirror.Mirror` has a method per operation:
:meth:`~pygitmirror.mirror.mirror.Mirror.clone`,
:meth:`~pygitmirror.mirror.mirror.Mirror.sync` and
:meth:`~pygitmirror.mirror.mirror.Mirror.migrate`. Each takes the repository
at the source as ``"owner/name"`` or as a
:class:`~pygitmirror.repository_ref.RepositoryRef`, and returns a
:class:`~pygitmirror.mirror.mirror_result.MirrorResult`.

.. code-block:: python

   preview = mirror.sync("my-org/api", dry_run=True)
   print(len(preview.plan.create), len(preview.plan.update), len(preview.plan.delete))

   mirror.clone("my-org/api", to="other-org/api-copy")
   mirror.migrate("my-org/api", archive_source=True)

The destination has the name of the source unless ``to`` names another one.
To rename owners for all repositories, give the mirror a mapping:
``Mirror(source, destination, owners={"my-org": "team"})``.

Many repositories
-----------------

:meth:`~pygitmirror.mirror.mirror.Mirror.run` applies an operation to
several repositories and yields each result as soon as it is known. A
failure does not stop the others; it is in the ``error`` of its result.

.. code-block:: python

   from pygitmirror import Operation

   for result in mirror.run(Operation.SYNC, mirror.repositories("my-org")):
       if not result.ok:
           print("failed:", result.source, result.error)
       elif result.changed:
           print(result.summary())

Results as data, and the local mirrors
--------------------------------------

A result which failed has ``result.error``, the exception, and
``result.advice``: a sentence which says what went wrong and what to do,
for the failures which are common, such as a repository which does not
exist or a token which is refused.

``result.to_dict()`` gives a result as plain data, ready to be stored or
sent as JSON. ``mirror.forget("my-org/api")`` deletes the local mirror of a
repository to free its disk space; the next operation downloads it again.

Errors
------

The single-repository methods raise. All errors derive from
:class:`~pygitmirror.errors.GitMirrorError`:

.. list-table::
   :widths: 30 70

   * - :class:`~pygitmirror.errors.GitError`
     - a git command failed; ``output`` has what git said
   * - :class:`~pygitmirror.errors.ApiError`
     - a request to a host failed; ``status`` has the HTTP status
   * - :class:`~pygitmirror.errors.DivergedError`
     - a clone or migration would have to overwrite ``refs``
   * - :class:`~pygitmirror.errors.VerificationError`
     - the destination of a migration does not equal the source
   * - :class:`~pygitmirror.errors.EmptySourceError`
     - a sync would delete everything at the destination
   * - :class:`~pygitmirror.errors.UnsupportedError`
     - the host cannot do what was asked
   * - :class:`~pygitmirror.errors.ConfigError`
     - a name, URL or setting is invalid

Running as a service
--------------------

The library is written to be driven by a long-running program:

* Nothing is global. A :class:`~pygitmirror.mirror.mirror.Mirror` holds no
  state between calls, so one process can serve many accounts.
* git never waits for input, so a missing credential fails instead of
  hanging.
* Without a ``workdir`` each call uses a temporary folder and removes it.
* When addresses come from users, restrict the transports of git, so that
  an address cannot name a local folder or a command:

  .. code-block:: python

     from pygitmirror import Git

     mirror = Mirror(source, destination, git=Git(allowed_protocols=("https", "ssh"), timeout=3600))

Two calls must not use the same local mirror at the same time: give
concurrent jobs for the same repository different ``workdir`` folders, or
run them one after the other.

The page of the package, :doc:`web`, is such a program, in
``pygitmirror.web``. ``WebApp`` can be served by another HTTP server
through its ``handle`` method.

Logging
-------

The package logs to the logger ``pygitmirror`` and configures nothing. At
``INFO`` it logs each operation and each change of a host; at ``DEBUG``
every git command and request. Tokens are never logged.
