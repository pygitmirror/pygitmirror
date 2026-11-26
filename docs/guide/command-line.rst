Command Line
============

.. code-block:: text

   git-mirror {clone,sync,migrate} [options]
   git-mirror serve [options]

The first three commands are the operations; see :doc:`operations`.
``git-mirror COMMAND --help`` lists their options, which are the same for
all three except where noted. ``serve`` runs the page and is described in
:doc:`web`.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Option
     - Meaning
   * - ``--config FILE``
     - a settings file; see below
   * - ``--source PROVIDER``, ``--destination PROVIDER``
     - the service: ``github``, ``gitlab``, ``gitea``, ``bitbucket`` or
       ``plain``, which is the default
   * - ``--source-url URL``, ``--destination-url URL``
     - the address of the server, when the provider has no default or you
       run your own
   * - ``--source-git-url URL``, ``--destination-git-url URL``
     - the address for git when it differs, such as ``ssh://git@github.com``
   * - ``--source-username NAME``, ``--destination-username NAME``
     - the user name sent with the token, when the host needs one
   * - ``--source-token-env VARIABLE``, ``--destination-token-env VARIABLE``
     - the environment variable of the token, instead of
       ``GIT_MIRROR_SOURCE_TOKEN`` and ``GIT_MIRROR_DESTINATION_TOKEN``
   * - ``--org OWNER``
     - the owner of the repositories at the source
   * - ``--repo NAME [NAME ...]``
     - the names of the repositories
   * - ``--all``
     - all repositories of the owner, instead of ``--repo``
   * - ``--destination-org OWNER``
     - the owner at the destination, when it is not named the same
   * - ``--sync-path FOLDER``
     - the folder of the local mirrors; the current folder by default
   * - ``--dry-run``
     - report what would be done without changing anything
   * - ``--no-prune``
     - ``sync`` only: keep the branches and tags which the source does not
       have
   * - ``--archive-source``
     - ``migrate`` only: make the source read-only once the copy is checked
   * - ``--log LEVEL``
     - ``DEBUG``, ``INFO`` (the default), ``WARNING``, ``ERROR`` or
       ``CRITICAL``. ``DEBUG`` shows every git command and request.

Settings file
-------------

A settings file names the hosts and many repositories at once. It is JSON,
in which a line starting with ``//`` is a comment:

.. code-block:: text

   {
     "sync_path": "/var/lib/git-mirror",
     "source": {
       "provider": "github",
       "token_env": "GITHUB_TOKEN"
     },
     "destination": {
       "provider": "gitea",
       "url": "https://git.example.com",
       "git_url": "ssh://git@git.example.com:2222",
       "token_env": "GITEA_TOKEN"
     },
     "repos": {
       // These two only.
       "organization-1": ["repo-1", "repo-2"],
       // Every repository of the organization.
       "organization-2": "*"
     },
     "owners": {
       "organization-1": "team-1"
     }
   }

.. code-block:: bash

   git-mirror sync --config settings.json

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Key
     - Meaning
   * - ``source``, ``destination``
     - the hosts, with the keys ``provider``, ``url``, ``git_url``,
       ``username`` and ``token_env``, which mean what the options of the
       same names mean
   * - ``repos``
     - the names of the repositories by owner at the source, or ``"*"`` for
       all repositories of an owner
   * - ``owners``
     - the owner at the destination for each owner at the source which is
       not named the same there
   * - ``sync_path``
     - the folder of the local mirrors
   * - ``prune``
     - ``false`` to keep, in a sync, what the source does not have
   * - ``archive_source``
     - ``true`` to archive the source of a migration
   * - ``source_url``, ``destination_url``
     - the addresses of two plain git servers, as in the files of the first
       versions of the package

An option given on the command line wins over the file. ``--org`` with
``--repo`` or ``--all`` replaces the ``repos`` of the file.

A file with a key which is not in this table is rejected. There is no key
for a token.

Exit status
-----------

.. list-table::
   :widths: 10 90

   * - 0
     - every repository succeeded
   * - 1
     - at least one repository failed; the others were still processed
   * - 2
     - the options or the settings are invalid, or nothing could be started

Running without a command
-------------------------

The first versions of the package had no commands. A call without one, such
as ``git-mirror --source_url ... --destination_url ... --org ... --repo
...``, still works and runs ``clone``, which is closest to what those
versions did. The option names with underscores are accepted as well.
