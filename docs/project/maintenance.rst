Maintenance Notes
=================

What was learned while building the package, written down so that it does
not have to be learned again.

Trying a host
-------------

What is known about each host, and what was verified against the real
service, is in :doc:`host-notes`. To try a host, with or without a token:

.. code-block:: python

   from pygitmirror import Git, RepositoryRef, make_host
   from pygitmirror.git import default_branch, list_refs

   host = make_host("github", token=None)  # or a token
   repository = RepositoryRef("git", "git")
   print(host.get_repository(repository))
   print(len(host.list_repositories("git")))
   url = host.repository_url(repository)
   print(default_branch(Git(), url, host.git_config()))
   print(len(list_refs(Git(), url, host.git_config())))

Use a repository made for the purpose when trying what changes a host.

git
---

* **Configuration in the environment needs git 2.31.**
  ``GIT_CONFIG_COUNT`` is what carries the token; older versions ignore it
  and the push fails for lack of credentials.
* ``git ls-remote --refs`` leaves out ``HEAD`` and the second line which an
  annotated tag has, with ``^{}`` at the end, so that a listing has one line
  per branch and tag.
* **A fetch with a URL and refspecs prunes** what matches the refspecs,
  as it does for a configured remote. No remote is needed.
* **A push of** ``refs/tags/*`` **with no tags** succeeds and does nothing.
* ``merge-base --is-ancestor`` exits with 1 when the answer is no and
  with 128 when it does not know a commit. Both mean that a branch cannot
  simply be moved forward.
* ``GIT_ALLOW_PROTOCOL`` **applies to local paths**, as the ``file``
  protocol. The tests use local paths, so they need ``file`` allowed.
* **git marks its object files read-only**, and Windows refuses to delete
  a read-only file. ``remove_tree`` makes such a file writable first.
  Deleting with errors ignored left the local mirrors in place on
  Windows, which only the Windows jobs of CI showed.
* **A bare repository lets its default branch be deleted** unless
  ``receive.denyDeleteCurrent`` is set. The hosts refuse, which the test of
  a renamed default branch imitates with that setting.

The standard library
--------------------

* ``urllib`` **follows redirects and keeps the headers**, the
  ``Authorization`` header included. ``_SameOriginRedirects`` stops at the
  border of the server; the response then has the status of the redirect,
  which the client reports as an error.
* ``logging.basicConfig(force=True)`` removes the handlers of the test
  runner. The command does not use it.

The page
--------

* **To look at the page without a screen**, run a headless browser in a
  container (``chromedp/headless-shell``, with its debugging port
  published) and drive it over its debugging protocol: set the width and
  the color scheme, open the page, and capture a screenshot. Its own
  ``--screenshot`` option never returned, in a container and on macOS
  alike. The browser reaches a page on the machine as
  ``host.docker.internal``, which the page must be told to allow with
  ``--allow-host``.
* **Scripts and styles are served with** ``no-cache``. With a lifetime, a
  browser kept running the scripts of the version before.
* **Setting a style from a script is allowed** by the content policy;
  a ``style`` attribute in the markup is not.
* **The modules of the page import each other by relative name**, such as
  ``./dom.js``, which the server serves from ``/static/``. A file in a
  subfolder would not be served.
* **The access key in a test is fixed**; in use it is random at each
  start, which logs every browser out. ``GIT_MIRROR_KEY`` fixes it.

The image
---------

* **It is about 65 MB of files**, half of them Python; Docker reports
  about 100 MB.
* **The version is given to the build as an argument**, since the git
  tags are not in the build context.
* **A version between releases has a plus sign**, which a tag of an image
  cannot have. Only releases are pushed.
* **Inside a container** ``localhost`` **is the container.** A server on
  the machine is ``host.docker.internal``.

The workflows
-------------

* The docs show "development version" unless they are built from a release
  tag, which needs the tags: the ``Quality`` workflow and Read the Docs
  fetch the full history.
* On Windows the jobs run ``make`` in bash, which the runners have.
