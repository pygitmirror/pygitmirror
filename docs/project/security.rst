Security
========

What the package defends against, and where each defense is. To report a
vulnerability, see ``SECURITY.md`` in the repository.

What is at stake
----------------

* **Tokens** which can read and write every repository of an account.
* **The repositories**: an operation can overwrite or delete branches at
  the destination, and archive the source.
* **The machine** which runs the package: it starts git, writes to a
  folder, and connects to addresses it is given.

Tokens
------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - A token could leak through
     - What prevents it
   * - a URL, which git stores in the repository and prints in errors
     - no URL with a token is ever built; the token is an HTTP header
       given to git in the environment of one command
   * - the list of processes
     - the header is in the environment, not in the arguments
   * - a file
     - nothing writes a token; the local mirror has no remotes
   * - a redirect or a link to another server
     - the API client follows neither off its own server
   * - a log or an error message
     - text passes through ``redact()``; headers and environments are
       never logged
   * - the settings file or the shell history
     - the command reads tokens from environment variables only
   * - the browser
     - the page keeps a token in a form field only: not in storage, not in
       a cookie, and the field asks password managers not to save it
   * - a finished job of the page
     - a job drops the hosts, and with them the tokens, when it ends

Input
-----

Names and addresses are checked where they enter.

* ``RepositoryRef`` accepts letters, digits and ``_ . ~ -`` in a name, no
  ``..`` and no leading hyphen: a name cannot leave the folder of the
  local mirrors or be read by git as an option.
* git is started with a list of arguments, never through a shell, and with
  ``GIT_ALLOW_PROTOCOL`` set: an address cannot use the ``ext`` transport,
  which runs a command.
* The page accepts ``http`` and ``https`` addresses, and ``ssh`` for git.
  It refuses local folders and addresses with credentials in them, and
  gives git no ``file`` transport.
* The page reads every field through ``web/_forms.py``: types, lengths and
  the number of repositories are limited, and a request body is at most
  64 KB.
* What a server answers, such as a repository name or an error, is put
  into the page as text and never parsed as HTML.

The page
--------

The page gives whoever reaches it the power to use tokens and change
repositories, so reaching it is what is protected.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Threat
     - Defense
   * - Another machine on the network
     - it listens on ``127.0.0.1`` unless told otherwise; the Docker
       instructions publish the port to the local machine only
   * - Another user or program on the machine
     - every request to the API needs the access key: 32 random bytes, new
       at each start, compared in constant time, kept in a cookie which
       scripts cannot read
   * - A website open in the same browser sending requests (CSRF)
     - the cookie is ``SameSite=Strict``; a request which changes
       something must be JSON, carry a header which a page of another site
       cannot send without permission, and have no foreign ``Origin``
   * - A website making the browser resolve its own name to this machine
       (DNS rebinding)
     - requests whose ``Host`` is not a local name, or one allowed with
       ``--allow-host``, are refused
   * - Injected script or markup
     - the content policy allows scripts, styles and fonts from the page
       itself only, and nothing inline; a test checks the files for it
   * - Being framed by another page
     - ``frame-ancestors 'none'`` and ``X-Frame-Options: DENY``
   * - Reading files of the machine through the server
     - a request can only name one of the files of the page, which are
       read once at start; no path of a request reaches the file system
   * - The key in the address bar or the history
     - the first visit exchanges it for the cookie and redirects; the
       server does not log the first line of requests

What it does not defend against: the page is served over plain HTTP and
has one key and no accounts. It is not for the internet, and not for
sharing. Someone who can read the memory of the process, or the traffic of
the local machine, can read tokens.

The image
---------

* Built on bare Alpine with Python, git and the SSH client; no package
  manager for Python, no compiler.
* Runs as a user which is not root, needs no capabilities, and works with
  a read-only file system and a temporary ``/tmp``.
* Writes only to ``/data``.
* Its base image and the actions of the workflows are updated monthly by
  Dependabot.

Operations
----------

* Clone and migrate cannot overwrite or delete at the destination; sync
  can, and the page asks before it does.
* A sync refuses to empty a destination because the source is empty.
* Every operation has a preview which changes nothing.
* A repository whose visibility is unknown is created private.
* Nothing deletes a repository. The source can be archived, which can be
  undone.

The project
-----------

* No dependencies at run time, so no supply chain beyond Python and git.
* ``ruff`` runs the security rules of bandit on every change, ``mypy``
  runs in strict mode, and CodeQL scans the code and the workflows.
* Workflows have read-only permissions unless a job needs more, and the
  release is uploaded with trusted publishing: no stored secret.
