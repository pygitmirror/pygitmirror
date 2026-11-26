Roadmap
=======

The work which is open, in the order it will be done. This page is the
list of record: an item which is done is removed from it and goes to the
:doc:`changelog`; work which is found or put off is added here.

The rule for all of it: **one thing at a time, finished and verified
before the next.**

Now: the first version
----------------------

The first version copies between plain git servers, Gitea or Forgejo, and
GitLab, in any combination. Each was run against a real server with
tokens; the Gitea copy is repeated on every pull request. What is missing
before it is released:

* **Errors a person can act on.** A repository which does not exist is
  reported with the raw message of git. Say what is wrong and what to do
  for the common cases: not found, not allowed, no space, diverged.
* **Forgejo**, which shares the API: run the same check against it.
* **Syncs to GitLab.** GitLab protects the default branch of a new
  project, and refuses a sync which rewrites it. Let the destination allow
  forced pushes when a sync asks for it, or say exactly what to change.
* **A repeatable check for GitLab**, as ``make check-gitea`` is for Gitea.
  It was run by hand; the server takes minutes to start, so it may run on
  a schedule instead of on every pull request.
* **Git over SSH in the image.** It needs a key and the known hosts in
  the container; decide how they are given, and try it.
* **Publish the image** with the next release, and add a picture of the
  page to the README.

Next: the page, a little further
--------------------------------

* **Progress within a repository.** A large repository takes minutes; the
  page only shows "waiting". git reports progress which can be passed on.
* **Stopping a job.**
* **Space before starting.** Gitea reports the size of a repository;
  compare the sum with the free space and warn before the copy.
* **Remember the servers**, not the tokens, between visits.
* **A lock on the local mirror**, so that the command and the page, or two
  pages, can share a folder.
* **Retries when a host limits requests** (HTTP 429, and GitHub's 403
  with its headers).

Then: the hosts, one by one
---------------------------

Each host follows the steps in the instructions for contributors: study
how other tools handle it, implement, verify against the real service as
source and as destination, and only then offer it in the page. In this
order:

1. **GitHub**, which is in the library and waits for verification
2. **Bitbucket Cloud**, likewise
3. **gitlab.com and Codeberg**, the public servers of hosts which are
   verified on servers of our own: verification only
4. **Gogs**
5. **Bitbucket Data Center**, which has an API of its own
6. **Azure DevOps**
7. **Gitee**
8. **OneDev**
9. **SourceHut**
10. **AWS CodeCommit**

More to copy, once the hosts are stable
---------------------------------------

Code first, everything else after it, and again one host at a time.

* **Git LFS files.** The pointers are copied and the files are not, which
  leaves a destination broken for repositories which use LFS.
* **Wikis.** A wiki is a second git repository on every host.
* **Topics, the home page, and whether issues are enabled.**
* **Issues**, one pair of hosts at a time, starting with Gitea to Gitea.
  Each host has its own model of labels, milestones, authors and dates;
  an issue copied by a token is written by the owner of the token.
  Decide first what is kept and what is said about the rest.
* **Pull requests**, after issues, in the same way. They refer to
  branches and commits, which must be there first.
* **Releases and their files.**

Storage
-------

* **Local copies in cloud storage**: S3 first, then Google Cloud Storage
  and Azure Blob Storage, so that a container without a large disk can
  keep its copies and sync quickly. A bare repository is many small files
  which git must read locally, so this means packing a copy into one
  object after a job and unpacking it before the next, not mounting a
  bucket. It needs a decision on the dependency, since the package has
  none.
* **A limit on the space of the copies**, deleting the least recently used.

Scheduling
----------

* **Sync on a schedule from the page.** Today a schedule is ``cron`` and
  the command. In the page it needs stored tokens, which needs a decision
  on how they are encrypted and where the key is.
* **Sync when the source changes**, through a webhook.

Not planned
-----------

* A hosted service with accounts. The package is a tool one person runs.
* Copying in both directions at once. A sync has a source and a
  destination.
* Deleting repositories.

Project
-------

* **Let the daily tests open an issue when they fail.** A scheduled run
  which fails only shows in the Actions tab.
* **A page titled with the version on Read the Docs**, by activating the
  tags there.
