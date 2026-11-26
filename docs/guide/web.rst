The Page
========

``git-mirror serve`` serves a page which does in a browser what the command
does in a terminal: choose two servers, name the repositories, preview, and
run. It is for one person on their own machine.

.. note::

   The page offers Gitea and Forgejo, GitLab, and plain git servers. The
   other hosts of the library are added to it one by one, as each is
   verified; see the :doc:`/project/roadmap`. The command has all of them.

Running it
----------

.. code-block:: bash

   git-mirror serve

It prints a link which ends in ``?key=…``. Open the link once: the browser
keeps the key in a cookie, and the page works until the server is
restarted, which makes a new key.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - Meaning
   * - ``--port PORT``
     - the port to listen on; 47417 by default
   * - ``--host ADDRESS``
     - the address to listen on; ``127.0.0.1`` by default, which only this
       machine can reach
   * - ``--allow-host NAME``
     - a host name the page may be reached under, besides ``localhost``;
       needed when it is opened under another name
   * - ``--sync-path FOLDER``
     - where the local copies are kept; by default ``git-mirror`` in the
       cache folder of the user, which is ``~/.cache/git-mirror`` unless
       ``XDG_CACHE_HOME`` or, on Windows, ``LOCALAPPDATA`` says otherwise.
       The page shows the folder, and the server logs it when it starts.

Set the environment variable ``GIT_MIRROR_KEY`` to choose the key yourself,
so that the link stays the same from one start to the next.

Running it with Docker
----------------------

.. code-block:: bash

   docker run -d --name git-mirror \
       -p 127.0.0.1:47417:47417 \
       -v git-mirror-data:/data \
       --add-host host.docker.internal:host-gateway \
       ghcr.io/pygitmirror/pygitmirror

   docker logs git-mirror    # shows the link to open

Each part matters:

``-p 127.0.0.1:47417:47417``
   Publishes the page to this machine only. Without ``127.0.0.1`` everyone
   on your network can reach the port.

``-v git-mirror-data:/data``
   Keeps the local copies in a volume. Without it they are in the
   container and are lost when it is removed, and every sync downloads
   everything again. See `Disk space`_ for how large it must be.

``--add-host host.docker.internal:host-gateway``
   Lets the container reach servers which run on your machine. Inside a
   container ``localhost`` is the container itself: a server at
   ``http://localhost:3000`` is entered in the page as
   ``http://host.docker.internal:3000``. A server in another container is
   reached by its name when both are on the same Docker network.

The repository has a ``compose.yaml`` which does the same and also makes
the file system of the container read-only and drops its privileges:

.. code-block:: bash

   docker compose up -d && docker compose logs git-mirror

The image holds Alpine Linux, Python, git, the SSH client and the package.
It runs as a user which is not root. Use HTTP or HTTPS addresses with
tokens in the image; git over SSH needs a key and the known hosts inside
the container, which has not been set up or tried yet.

Disk space
----------

A repository does not go from server to server directly. It passes through
a copy on the machine which runs the page, so **the largest repository you
can copy is limited by the free space of that folder or volume**.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * -
     - Copies kept (the default)
     - Copies deleted after each repository
   * - Space needed
     - the sum of all repositories
     - the largest repository
   * - The next sync
     - downloads only what is new
     - downloads everything again
   * - Use it for
     - keeping servers in sync
     - a migration which is done once

A local copy is about as large as the repository is on its server: the
history, compressed, without checked-out files. The page shows how much the
copies use and how much is free, and warns when less than 1 GB is free.
"Delete the local copies" frees the space; nothing but speed is lost.

A copy which ran out of space fails with the message of git, and leaves
both servers as they were. Free some space and run it again.

Using it
--------

1. **Servers.** Choose the kind of each server and enter its address and
   an access token; :doc:`hosts` says what a token must be allowed to do.
2. **Repositories.** Enter the owner at the source. "List repositories"
   fills in every repository of the owner; remove the lines you do not
   want, or type the names. Enter another owner for the destination when
   it is not named the same there.
3. **Operation.** Choose clone, sync or migrate; :doc:`operations` explains
   the difference.
   On GitLab an owner is a group, which may be nested: ``group/subgroup``.
   The owner at the destination must exist; it is not created.
4. **Preview** reads both servers and shows what would be created, updated
   and deleted, without changing anything. **Run** does it.

Results appear per repository as they finish. A repository which fails does
not stop the others. One job runs at a time.

What it protects, and what it does not
--------------------------------------

Tokens are typed into the page, sent to the program on your machine, used
for the two servers, and forgotten when the job ends. They are not written
to disk, not logged, and not kept by the browser.

The page is not built to be put on the internet or shared between people:
it has one key and no accounts, and it is served over plain HTTP. Keep it
on ``127.0.0.1``. :doc:`/project/security` describes the protections.
