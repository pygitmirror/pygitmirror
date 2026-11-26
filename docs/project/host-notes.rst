Host Notes
==========

What is known about each host: how it authenticates, what it limits, what
it refuses, and what has been tried against the real service. Read the
section of a host before working on it, and add to it what you learn.

Every statement here is marked by how it is known:

* **verified**: tried against the real service, with the date
* **documented**: taken from the documentation of the host, not tried
* **reported**: how other tools handle it, or common knowledge; to be
  checked when the host's turn comes

All hosts
---------

* Hosts keep references of their own which they refuse in a push:
  ``refs/pull/*`` on GitHub and Gitea, ``refs/merge-requests/*``,
  ``refs/keep-around/*`` and ``refs/pipelines/*`` on GitLab,
  ``refs/pull-requests/*`` on Bitbucket Data Center. This is why only
  ``refs/heads/*`` and ``refs/tags/*`` are copied. (reported)
* A host refuses to delete its default branch, so a sync sets the new
  default before it deletes the old one. (reported)
* A push to an archived repository is refused. (reported)
* ``git ls-remote --symref`` gives the default branch on every server,
  without the API. (verified 2026-11-25 on github.com, gitlab.com,
  gitea.com and bitbucket.org)

Gitea and Forgejo
-----------------

Offered in the page. Forgejo shares the API.

* API at ``/api/v1``; the token is sent as ``Authorization: token …``.
  (documented)
* For git over HTTPS the token is the password, with any user name.
  (documented)
* Reading a repository and listing an organization, over two pages, work
  without a token. (verified 2026-11-25 on gitea.com)
* A page has at most 50 items unless the server is configured otherwise;
  the next page is named by the ``Link`` header. (verified 2026-11-25)
* Organizations and users are different owners: a repository is created
  below ``/orgs/{name}`` or below ``/user``. (documented)
* A server can be set to create a repository on the first push to it.
  This is not relied on. (reported)
* Gitea can mirror by itself: its migration API creates a repository
  which pulls from another server on a schedule, and it can carry issues
  and pull requests from some hosts. Tools which copy only into Gitea use
  it. It is not used here, since it works in one direction and for one
  kind of destination. Worth revisiting when issues are added. (reported)
* With a token, against two servers of version 28.4 in containers
  (verified 2026-11-25, and by ``make check-gitea`` on every pull
  request): creating a repository in an organization and for the account;
  listing both, private repositories included; pushing over HTTP; clone,
  sync and migrate between the servers, with the description, the
  visibility and the default branch carried over; following a renamed
  default branch; archiving the source; and that a private repository is
  hidden without a token.
* The same through the page running in its image, with the servers
  reached by their container names. (verified 2026-11-25)
* An organization or user which does not exist is not created: the
  destination owner must exist. (verified 2026-11-25)
* **Not verified:** git over SSH, Forgejo, and a server behind HTTPS.

GitHub
------

In the library and the command; not offered in the page yet.

* API at ``api.github.com``, or ``/api/v3`` on GitHub Enterprise Server.
  (documented)
* For git over HTTPS the user name is ``x-access-token`` and the token is
  the password. (documented)
* Reading a repository, listing an organization and a user, and git over
  HTTPS work without a token. (verified 2026-11-25)
* Without a token the API allows 60 requests an hour; with one, 5,000.
  Creating many repositories quickly meets a second, undocumented limit.
  (documented, and reported)
* A push with a file over 100 MB is refused, and a single push is limited
  in size; tools push large repositories in several parts. (documented,
  and reported)
* A push which contains something that looks like a secret can be refused
  by push protection. (documented)
* A renamed repository answers under its old name with a redirect.
  (documented)
* **Not verified:** anything with a token.

GitLab
------

Offered in the page.

* API at ``/api/v4``; a project is named by its path with the slashes
  encoded. (verified 2026-11-25 for reading)
* For git over HTTPS the user name is ``oauth2``. (documented)
* Owners are groups, which nest, or users; both are namespaces, and a
  project is created with the number of its namespace. (documented)
* The default branch of a new project is protected against forced pushes,
  so a sync of rewritten history is refused until that is allowed.
  (documented)
* The visibility "internal" has no counterpart elsewhere and is copied as
  private. (documented)
* A deleted project may be kept for some days, during which its path is
  taken. (reported)
* With a token, against a self-managed server of the Community Edition
  in a container (verified 2026-11-25, by hand): creating a project in a
  nested group and for the user; listing a group, without the projects of
  its subgroups, and a user, private projects included; pushing over HTTP
  with ``oauth2`` as the user name; clone and sync to and from Gitea, and
  from group to group on one server; setting the default branch;
  migrating with the source archived; and "internal" read as private.
* A sync which rewrites the default branch of a GitLab destination is
  refused: "You are not allowed to force push code to a protected branch".
  (verified 2026-11-25) Until the package can lift that protection, allow
  forced pushes for the branch in the settings of the project.
* A group which does not exist is not created. (verified 2026-11-25)
* **Not verified:** gitlab.com itself with a token, group and project
  access tokens, and git over SSH. The check is not repeated in CI: the
  server takes minutes to start.

Bitbucket Cloud
---------------

In the library and the command; not offered in the page yet.

* API at ``api.bitbucket.org/2.0``; owners are workspaces and names are
  slugs in lower case. (documented)
* Lists are objects with ``values`` and the address of the ``next`` page.
  (verified 2026-11-25 for the first page; the second timed out)
* Access tokens of a workspace, project or repository are sent as bearer
  tokens, with ``x-token-auth`` as the user name for git. API tokens and
  app passwords of a user need the user's name. (documented)
* A repository cannot be archived. (documented)
* Whether a ``PUT`` with only ``mainbranch`` changes the default branch
  and nothing else is not known. (to be tried)
* **Not verified:** anything with a token.

Plain git servers
-----------------

* Any server which git can reach, with nothing but git: no listing, no
  creating, no settings.
* The tests copy between bare repositories in folders, which is the same
  code with the ``file`` transport. (verified by the tests)
* A bare repository lets its default branch be deleted unless
  ``receive.denyDeleteCurrent`` is set.
