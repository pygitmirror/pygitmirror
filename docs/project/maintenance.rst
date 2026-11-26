Maintenance Notes
=================

What was learned while building the package, written down so that it does
not have to be learned again.

What was verified against the real services
-------------------------------------------

On 2026-11-25, without tokens, against public repositories:

.. list-table::
   :header-rows: 1
   :widths: 22 26 26 26

   * - Host
     - Reading a repository
     - Listing an owner
     - git over HTTPS
   * - github.com
     - works
     - works, organization and user
     - works
   * - gitlab.com
     - works
     - works, nested group
     - works
   * - gitea.com
     - works
     - works, over two pages
     - works
   * - bitbucket.org
     - works
     - the first page works; the second timed out
     - works

**Not verified against any real service:** everything which needs a token.
That is authentication of the API and of git, creating a repository,
changing the default branch, archiving, and listing private repositories.
These are tested against stand-ins written from the documentation of the
APIs. In particular:

* Bitbucket: that a ``PUT`` with only ``mainbranch`` changes the default
  branch and nothing else, and which user name each kind of token needs
  for git.
* Gitea: that ``/users/{name}/repos`` and ``/user/repos`` include private
  repositories for the account of the token.
* GitHub Enterprise Server and self-managed GitLab were not reached at
  all; they should behave like the public servers under another address.

Trying them is the first item of the :doc:`roadmap`. Update this section
when it is done.

To repeat the check, or to try a host with a token:

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

The workflows
-------------

* The docs show "development version" unless they are built from a release
  tag, which needs the tags: the ``Quality`` workflow and Read the Docs
  fetch the full history.
* On Windows the jobs run ``make`` in bash, which the runners have.
