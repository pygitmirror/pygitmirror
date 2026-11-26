Quickstart
==========

This page copies the repositories of a GitHub organization to a Gitea
server and keeps them up to date.

1. Create the tokens
--------------------

Create an access token on each host; :doc:`/guide/hosts` says what each one
must be allowed to do. Give them to ``git-mirror`` through the environment:

.. code-block:: bash

   export GIT_MIRROR_SOURCE_TOKEN=github_pat_...
   export GIT_MIRROR_DESTINATION_TOKEN=...

A token is never given as an option or stored in a settings file: an option
is visible to every user of the machine, and a file gets shared.

2. See what would happen
------------------------

.. code-block:: bash

   git-mirror sync --dry-run \
       --source github \
       --destination gitea --destination-url https://git.example.com \
       --org my-org --all

``--dry-run`` reads both hosts and reports, for every repository, whether it
would be created and how many branches and tags would be created, updated
and deleted. Nothing is changed.

3. Copy
-------

Run the same command without ``--dry-run``. Each repository is reported on
one line, and one which fails does not stop the others::

   sync my-org/api -> my-org/api: repository created, 14 created, 0 updated
   sync my-org/web -> my-org/web: repository created, 31 created, 0 updated
   0 of 2 repositories failed

The exit status is 0 when every repository succeeded and 1 when one failed.

4. Keep in sync
---------------

Run the command again whenever the copy should catch up, for example every
hour from ``cron``. A repository which did not change costs two short
requests and downloads nothing.

Local mirrors of the repositories are kept in the current folder, in
``my-org/api.git`` and so on, so that a later run only downloads what is
new. Choose another folder with ``--sync-path``.

Next
----

* :doc:`/guide/operations` for the difference between clone, sync and
  migrate
* :doc:`/guide/command-line` for the settings file, which names many
  repositories at once
* :doc:`/guide/library` to do the same from Python
