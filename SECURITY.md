# Security policy

`pygitmirror` handles access tokens for git hosts, runs the `git` executable, sends requests to the APIs of the hosts it is told to use, and can serve a page on the local machine. [The security page](https://pygitmirror.readthedocs.io/en/latest/project/security.html) of the documentation describes what it defends against and how.

A vulnerability is, for example:

- a token which reaches a file, a URL, a command line, a log or a server other than the one it belongs to
- a repository name, URL or setting which makes the package run a command, or read or write outside the folder of its local mirrors
- an operation which changes or deletes more than its documentation says
- a way to use the page without its access key, from another site, or under another host name

The package gives git the transports `https`, `http`, `ssh`, `git` and `file` by default. A service which takes addresses from its users must restrict them, as the [library guide](https://pygitmirror.readthedocs.io/en/latest/guide/library.html) describes; that local folders can be read with the default is intended. The page restricts them itself.

The page is for one user on one machine. That it is served over plain HTTP, has a single key and should not be exposed to a network is intended and documented.

## Supported versions

Fixes are released for the latest version on [PyPI](https://pypi.org/project/pygitmirror/) only. Upgrade to it before reporting.

## Reporting a vulnerability

Do not open a public issue. Report privately with [Report a vulnerability](https://github.com/pygitmirror/pygitmirror/security/advisories/new) on the Security tab of the repository, with:

- the versions of `pygitmirror`, Python and git
- the command or a short piece of code which shows the problem
- what an attacker could do with it

You can expect an answer within a week. When a report is confirmed, the fix is released as a new version, and an advisory which credits you, if you wish, is published with it.

A problem which is not a vulnerability, such as a failed push or a wrong message, is an ordinary bug: open an [issue](https://github.com/pygitmirror/pygitmirror/issues).
