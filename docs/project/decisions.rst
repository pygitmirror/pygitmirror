Decisions
=========

Choices which shaped the package, with their reasons. Read this page before
proposing to change one of them, and add an entry when a choice is made
which someone could later question: what was chosen, what the alternative
was, and why.

The package
-----------

**No dependencies.**
   git is run as a program, and the APIs are called with ``urllib``. The
   alternatives were GitPython, which the first versions used, and an HTTP
   library. GitPython needs the git executable as well and was used for
   three calls; the four APIs need a dozen plain JSON requests. A tool
   which is installed on servers and build machines should install
   anywhere and have nothing to update.

**The git executable, not a git library.**
   The protocol, authentication, proxies and SSH of the user's git are what
   they have configured and tested. A reimplementation would behave
   differently in exactly the cases which are hard to debug.

**Python 3.11 and newer.**
   Python 3.10 reached its end of life in October 2026.

**One class per module, and no file over 300 lines.**
   A host, the plan, the result: each is found by its name, and each file
   can be read in one sitting. The limit holds for every file which is
   written by hand, documentation and style sheets included. Exceptions
   are the exception to the first rule: they have no behavior and share
   ``errors.py``.

The operations
--------------

**Three operations which differ in what they may destroy.**
   Clone destroys nothing, sync overwrites and deletes, migrate also
   changes the source. The alternative was one operation with flags. With
   names, the dangerous choice is made by choosing a word, not by
   forgetting a flag.

**Only branches and tags are copied.**
   ``git clone --mirror`` copies every reference, including those which
   hosts keep for pull requests (``refs/pull``, ``refs/merge-requests``).
   Other hosts refuse them, which makes a mirror push fail.

**A clone moves branches forward.**
   Strictly adding would refuse a second clone after one new commit. Moving
   a branch forward loses nothing, and it is what ``git push`` does without
   force, which is what the first versions did.

**Divergence is checked before the push, not left to git.**
   git would reject the references which diverged and push the others,
   leaving the destination half updated. Checking first gives all or
   nothing, and a message which lists what differs.

**A sync does not empty the destination.**
   When the source has no branches or tags, deleting everything is what
   "make equal" means, and almost never what is wanted: the source was
   recreated, or the token sees an empty repository. It fails instead.

**A sync deletes after setting the default branch.**
   Two pushes instead of one, so that a renamed default branch can be
   followed. See :doc:`design`.

**The default branch is read with git, not through the API.**
   ``git ls-remote --symref`` works for every server, the plain ones
   included, and needs no permission beyond reading.

**A repository is created private unless the source is known to be public.**
   Without an API at the source, or without the right to read its
   settings, the visibility is unknown. Publishing by mistake cannot be
   undone; hiding by mistake can.

**Settings are copied at creation only.**
   The description and visibility of an existing destination are left
   alone: someone may have changed them on purpose.

**A migration does not delete the source.**
   It can archive it. Deleting is not reversible, and a verified copy of
   the branches and tags is not a copy of the issues.

**A failed repository does not stop a run.**
   One repository in a hundred with a file too large for the destination
   should not keep the other ninety-nine from being copied. The exit status
   says that something failed.

Credentials
-----------

**Tokens reach git through the environment of the command.**
   The alternatives leak: a URL with the token is stored in the repository
   and printed in errors; ``-c http.extraheader=...`` is visible in the
   list of processes; a credential helper writes to disk. See
   :doc:`design`.

**The command reads tokens from the environment only.**
   Not from an option, which is visible to other users and kept in the
   shell history, and not from the settings file, which gets committed. A
   settings file with a ``token`` key is rejected.

**Redirects to another server are not followed.**
   ``urllib`` would send the token to wherever a redirect points.

The command line
----------------

**Options win over the settings file.**
   The first versions had it the other way around. A file is the default,
   and an option is what the user asks for now.

**A call without a command runs clone.**
   The first versions had no commands and pushed without force, which is
   what clone does. Scripts written for them keep working and cannot start
   to overwrite.

**JSON with comment lines for the settings file.**
   It is the format of the first versions. TOML would be nicer and is in
   the standard library, but two formats would have to be kept.

**The local mirror is bare and named** ``<owner>/<name>.git``.
   The first versions kept a clone with a working tree in
   ``<owner>/<name>`` and checked out every branch. A working tree is not
   needed to push, and checking out is the slowest part for a large
   repository. The old folders are not used anymore and can be deleted.

The page
--------

**A page served by the package, not a separate application.**
   One thing to install and one image to run. The alternative, a web
   service with accounts, needs stored tokens, users and operations of
   its own, and is a different product.

**The server and the page use no framework.**
   The server is ``http.server`` of the standard library; the page is
   plain HTML, CSS and JavaScript modules. A web framework and a
   JavaScript toolchain would each bring dependencies to keep current,
   for a dozen routes and one page. The price is doing the checks of
   ``_security.py`` by hand, each with a test.

**An access key in the link, as notebooks do.**
   Other programs and users of the machine can reach a local port. The
   key keeps them out without making the user choose a password.

**One job at a time.**
   Two jobs could fetch into the same local mirror at once. Until the
   mirror has a lock, the page refuses a second job.

**The page offers a host only once it is verified.**
   The library has classes for four services, tested against stand-ins.
   The page started with Gitea, GitLab and plain git servers, which were
   run against real servers, and gains the others one by one. A page invites people who cannot read a traceback.

**Port 47417.**
   The usual ports of local servers, such as 3000, 8000 and 8080, belong
   to whatever else the user is developing.

**The image is bare Alpine plus three packages.**
   Python, git and the SSH client are all it needs. An official Python
   image would bring pip and a second copy of what Alpine has.

**The page keeps its local copies in the cache folder of the user.**
   The command uses the current folder, as it always did. A page is
   started from anywhere, and would scatter folders where it was started.

**Tokens are not stored.**
   Typing a token for each job is a nuisance, and storing it needs
   encryption with a key which must live somewhere. That decision comes
   with scheduled syncs; see the :doc:`roadmap`.

The hosts
---------

**A plain host exists.**
   The first versions worked with any git server by URL. Keeping that as a
   host without an API means the operations need no special case for it.

**Bitbucket means Bitbucket Cloud.**
   Bitbucket Data Center has another API. It works as a plain host.

**GitLab's "internal" visibility is copied as private.**
   It has no counterpart elsewhere, and private is the safe side.
