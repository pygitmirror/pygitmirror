Operations
==========

An operation copies the branches and tags of a repository at the *source*
to a repository at the *destination*. There are three, and they share most
of what they do:

1. If the destination repository does not exist and its host has an API, it
   is created, with the description and the visibility of the source. When
   the visibility of the source is not known, it is created private.
2. The branches and tags of both are compared. If nothing has to change,
   the operation ends here, without downloading anything.
3. The source is fetched into a local mirror, which is pushed to the
   destination.

They differ in what they may change at the destination:

.. list-table::
   :header-rows: 1
   :widths: 34 22 22 22

   * -
     - clone
     - sync
     - migrate
   * - adds missing branches and tags
     - yes
     - yes
     - yes
   * - moves a branch forward
     - yes
     - yes
     - yes
   * - overwrites a branch or tag which differs
     - no, fails
     - yes
     - no, fails
   * - deletes what the source does not have
     - no, keeps it
     - yes
     - no, fails
   * - sets the default branch
     - when it creates
     - yes
     - yes
   * - checks the destination afterwards
     - no
     - no
     - yes
   * - can archive the source
     - no
     - no
     - yes

Only branches and tags are copied; see :ref:`what-is-not-copied`.

clone
-----

.. code-block:: bash

   git-mirror clone --source github --destination gitlab --org my-org --repo api

A clone only adds. It creates the branches and tags which the destination
does not have, and moves a branch forward when the source has new commits on
top of it. It never overwrites or deletes: a branch which has commits the
source does not have, or a tag which points elsewhere, makes it fail with a
list of what differs, before anything is pushed.

Use it for a first copy, and whenever the destination must not lose
anything.

sync
----

.. code-block:: bash

   git-mirror sync --source github --destination gitlab --org my-org --repo api

A sync makes the branches and tags of the destination equal to those of the
source. Run it again to catch up.

.. warning::

   A sync overwrites. Commits which exist only at the destination are lost,
   and branches and tags which the source does not have are deleted. The
   destination of a sync is a copy, not a place to work in.

* ``--no-prune`` keeps the branches and tags which the source does not have.
* The default branch of the destination follows that of the source, also
  when the source renames it.
* A source which has no branches or tags at all does not empty the
  destination: the sync fails. An empty source is more often a mistake than
  an intention.

On a host which protects the default branch against forced pushes, as
GitLab does for new projects, a sync of rewritten history is refused by the
host until the protection allows it.

migrate
-------

.. code-block:: bash

   git-mirror migrate --source bitbucket --destination github \
       --org my-workspace --destination-org my-org --all --archive-source

A migration moves a repository to a new home. It is a clone, followed by a
check that every branch and tag of the destination is the one of the
source, and no other exists. The default branch is set to that of the
source.

With ``--archive-source`` the source is then made read-only, so that nobody
keeps pushing to the old place. This is the last step, done only when the
check passed. Bitbucket and plain git servers cannot archive, which is
reported before anything is copied.

A migration can be repeated: one which was interrupted continues where it
stopped.

Dry runs
--------

Every operation takes ``--dry-run``, which reports what would be done and
changes nothing at either host. It still fetches into the local mirror when
there are differences, which is what a clone needs to tell a branch which
moved forward from one which diverged.

.. _what-is-not-copied:

What is not copied
------------------

* Issues, pull requests, wikis, releases and their files, webhooks,
  collaborators and branch protection.
* Files stored with Git LFS. The pointers are copied, the files are not.
* References other than branches and tags, such as those which hosts keep
  for pull requests, and git notes.

See the :doc:`/project/roadmap` for what is planned.
