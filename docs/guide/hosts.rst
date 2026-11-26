Hosts
=====

A host is a server which holds repositories, together with the account
used on it. ``pygitmirror`` knows four services and falls back to plain git
for everything else.

.. list-table::
   :header-rows: 1
   :widths: 14 30 20 12 12 12

   * - Provider
     - Servers
     - Owner of a repository
     - Creates
     - Lists
     - Archives
   * - ``github``
     - github.com, GitHub Enterprise Server
     - organization or user
     - yes
     - yes
     - yes
   * - ``gitlab``
     - gitlab.com, self-managed GitLab
     - group, also nested, or user
     - yes
     - yes
     - yes
   * - ``gitea``
     - Gitea, and Forgejo, which shares its API
     - organization or user
     - yes
     - yes
     - yes
   * - ``bitbucket``
     - bitbucket.org
     - workspace
     - yes
     - yes
     - no
   * - ``plain``
     - any git server, or a local folder
     - the first part of the path
     - no
     - no
     - no

The URL of the server is needed for ``gitea``, ``plain`` and a server you
run yourself; github.com, gitlab.com and bitbucket.org are the defaults of
their providers.

Tokens
------

A token is read from the environment: ``GIT_MIRROR_SOURCE_TOKEN`` for the
source and ``GIT_MIRROR_DESTINATION_TOKEN`` for the destination, or the
variables named with ``--source-token-env`` and ``--destination-token-env``.
It is used for the API and for git over HTTPS.

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Provider
     - What the token needs
   * - ``github``
     - A classic token with the ``repo`` scope, or a fine-grained token with
       read and write access to "Contents" and "Administration". Reading a
       source needs read access to "Contents" and "Metadata" only.
   * - ``gitlab``
     - The ``api`` scope. For a source which is only read, ``read_api`` and
       ``read_repository``.
   * - ``gitea``
     - The ``repository`` scope with write access, and ``organization`` and
       ``user`` with read access.
   * - ``bitbucket``
     - A workspace, project or repository access token with the
       ``repository:write`` and ``repository:admin`` scopes: give the token
       only. For an API token or an app password of a user, also give the
       user name which Bitbucket documents for it with
       ``--source-username`` or ``--destination-username``.

Archiving the source of a migration needs write access to the settings of
the source as well.

Git over SSH
------------

By default git uses HTTPS with the token. To use SSH, give the address for
git separately; the token is then used for the API only, and SSH
authenticates with your keys:

.. code-block:: bash

   git-mirror sync --source github --source-git-url ssh://git@github.com ...

The same option serves a server whose SSH port is not the default, such as
``ssh://git@git.example.com:2222``.

``git-mirror`` never waits for input. The host key of an SSH server must be
known already, and a key with a passphrase must be loaded in the agent;
otherwise the operation fails instead of hanging.

Plain git servers
-----------------

A plain host is reached through git only. The URL of a repository is the
address followed by the owner and the name, with nothing added:

.. code-block:: bash

   git-mirror clone \
       --source-url ssh://git@old.example.com:7999 \
       --destination-url https://git.example.com \
       --org my-project --repo api

reads ``ssh://git@old.example.com:7999/my-project/api``. Without an API
nothing can be created or listed: a destination repository must exist
already, and ``--all`` is not available. Credentials come from your git
configuration, as for any git command.

Use it for Bitbucket Data Center, Azure DevOps, Gerrit and bare
repositories in a folder.

Limits of the hosts
-------------------

* **GitLab** protects the default branch of a new project. A sync which
  rewrites it is refused until forced pushes are allowed for that branch.
* **GitLab** has a visibility between private and public, "internal". It is
  copied as private.
* **Bitbucket** cannot archive a repository.
* **GitHub** refuses a push with a file larger than 100 MB, which other
  hosts accept.

Only the reading requests were tried against the public servers; see
:doc:`/project/maintenance` for what was and was not verified.
