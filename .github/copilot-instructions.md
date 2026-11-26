# Instructions for coding agents

`pygitmirror` copies git repositories from one server to another. It is a Python library, the `git-mirror` command, and a page served on the user's own machine, also as a small Docker image. The first version covers plain git servers, Gitea and GitLab.

## What it is for

The niche, which decides what is built and what is not:

- **Any server to any other.** No host is special as a source or as a destination.
- **Safe by default.** A preview before every change; nothing is overwritten or deleted unless the user chose the operation which does that.
- **Code only, for now.** Branches and tags. Say so plainly wherever a user could expect more.
- **Runs locally.** One user, their machine, their tokens. Nothing is sent anywhere but to the two servers.

**Start small, in the tool and in the page.** Add one host, one option or one screen at a time, finish it, and verify it against a real server before the next. Do not build ahead of the roadmap.

## Where knowledge lives

Everything a contributor needs to know is in this repository. Keep it there: do not store rules, plans or decisions in a memory or notes of your own. A rule the maintainer gives which should hold from now on is written into this file in the same change.

| When you | Read | And update it when |
| --- | --- | --- |
| start any work | this file | you are given a standing rule |
| change how the parts work together | `docs/project/design.rst` | the structure or the steps of an operation change |
| touch the page or its server | `docs/project/ui-design.rst`, `docs/project/security.rst` | a component, a token or a protection changes |
| work on a host | `docs/project/host-notes.rst` | you learn a quirk, or verify something against the real service |
| look for what to do, or put something off | `docs/project/roadmap.rst` | work is finished, found or postponed |
| are about to choose between alternatives | `docs/project/decisions.rst` | a choice is made which someone could later question |
| work on git commands or a workflow | `docs/project/maintenance.rst` | you learn something the next person would have to learn again |

Do not reopen a decision recorded in `docs/project/decisions.rst` without a new reason; say what changed.

**The roadmap is always current.** In the same change as the work: remove what is done, and add what was found or put off. A finished item does not stay on the roadmap; it goes to the changelog.

## Commands

Everything runs through `uv` and the top-level `Makefile`. Do not add another task runner or per-folder make files. All dependencies, those of the docs included, are dependency groups in `pyproject.toml`; do not add requirements files. The package itself has no dependencies, and the page has no build step.

```shell
make install   # create the environment from uv.lock
make check     # lint, type check, test and build the docs: run it before you finish
make format    # format and apply the safe lint fixes
make serve     # run the page on this machine
make check-gitea  # copy between two real Gitea servers in containers; needs Docker
make           # list all targets
```

The workflows in `.github/workflows` call make targets only. A step which needs more than one command is a Python script in `.github/scripts` with a make target of its own, not shell in the workflow.

**Leave the common ports free.** Never listen on a port which other tools default to, such as 3000, 5000, 8000, 8080 or 8888: not as a default of the tool, not in tests, and not for anything you start while working. The page uses 47417 by default, and that port belongs to the maintainer as well: when you start the page or a test server yourself, give it another port near it, such as 47427.

## The design in brief

`docs/project/design.rst` is the full description. What must hold:

- **Layers, one direction.** `git` knows git and no host. `hosts` knows the services and no git. `mirror` combines them into the operations. `config` with `cli`, and `web`, are users of that library and are imported by nothing else.
- **One sequence of steps for all operations**, in `mirror/_transfer.py`. Clone, sync and migrate differ only in whether they overwrite, delete, verify and archive.
- **The order of the steps keeps a failure harmless**: nothing is deleted before everything was added, and the source is archived only after the copy was verified. A failed operation can be run again.
- **The local mirror equals the source** after a fetch, holds branches and tags only, and stores no address or credential. It is a cache: it can be deleted at any time.
- **A host is one class** derived from `Host`, registered in `hosts/_factory.py`. Operations must not test for a particular provider; they ask the host (`has_api`, `can_archive`).
- **The page adds no ability.** Whatever it does, the library does; the page only collects input and shows results.

## Rules for every file

- **No file has more than 300 lines.** Code, tests, documentation, style sheets, scripts, workflows, this file: all of them. A test checks it. Split a file before it reaches that size, into parts named after it and placed next to it. The exceptions are files nobody writes by hand: `uv.lock`, the generated diagrams, fonts and license texts.
- **American English** in code, comments, documentation and commit messages: color, behavior, modeling, analyze.
- **Standard tooling only.** `ruff` for lint and format, `mypy` in strict mode, `pytest`. No unusual configuration.

## Rules for the Python code

- **One public class per module**, named after it in snake case. Modules of helper functions without a public class start with an underscore, such as `_transfer.py`. Exceptions share `errors.py`.
- Every public module, class, method and function has a docstring with Sphinx field lists (`:param name:`, `:returns:`, `:raises Error:`). Types are in the hints, not in the docstrings.
- Mark an overriding method with `override` from `pygitmirror._compat`, which supports Python 3.11; it inherits the docstring.
- Errors which the package reports derive from `GitMirrorError`.

## Rules for the page

`docs/project/ui-design.rst` is the design system. What must hold:

- **Tokens only.** Every color, font and radius is a variable of `tokens.css`. No other file names a color or a font.
- **Light and dark** are both first-class, and every change is looked at in both.
- **No build step and nothing from elsewhere.** Plain HTML, CSS and JavaScript modules, served by the package. No framework, no bundler, no CDN, no font or script from another site.
- **Nothing inline.** No `style` attribute, no inline script, no event attribute: the content policy forbids them and a test checks it.
- **Text from a server is text.** Repository names and error messages are set with `textContent`, never parsed as HTML.
- **Motion is decoration**: at most 30 frames per second, stopped while out of sight, and a still picture when the reader asked for reduced motion.
- **Say what will happen** before it happens, in the words of the operations table. A destructive action asks first.

## Security

`docs/project/security.rst` lists the threats and what answers each. The rules which are easiest to break:

- **Tokens must not leak.** Never put a token in a URL, in an argument of a command, in a log, in a file or in the browser's storage. A host gives git its token through `Host.git_config()`, which `Git` passes in the environment of the command. The API client sends its headers to one server only.
- **Input is not trusted.** Build a repository name with `RepositoryRef`. Run git through `Git` only, never through a shell. The page reads what the browser sends through `web/_forms.py`, which validates every field.
- **The page is for one user on one machine.** It listens on the local address, needs the access key, refuses other host names and requests from other sites, and serves only its own files. Do not weaken one of these to make something convenient.
- **Destructive behavior is opt-in.** `clone` and `migrate` never overwrite or delete at the destination; only `sync` does. Only `migrate` with `archive_source` changes the source, and nothing ever deletes a repository. A new step which changes a host is skipped in a dry run. A repository whose visibility is unknown is created private.
- **The image stays small and unprivileged**: bare Alpine with Python, git and the SSH client, a user which is not root, a file system which may be read-only.

## Adding a host

One host at a time, in the order of the roadmap. A host is finished when all of this is done:

1. Read how the established tools which support it handle it, and the documentation of its API. Write what you learn into `docs/project/host-notes.rst`: authentication, limits, references it hides or refuses, anything which surprised those tools.
2. Implement the class as `docs/project/design.rst` describes, with tests against stand-ins.
3. Run clone, sync and migrate against the real service, as a source and as a destination. Record in the host notes what was verified, and never claim there what was not tried.
4. Only then offer it in the page (`OFFERED` in `web/_forms.py`), and update the guides.

Issues and pull requests come after the hosts are stable, again one host at a time.

## Tests

- git is real in the tests: they create repositories in a temporary folder and run git on them (`Workshop` in `tests/helpers.py`). Do not replace git with a stand-in.
- The APIs are stand-ins: `FakeTransport` answers requests from a table, `FolderHost` is a host with an API on folders. The tests need no network and no account.
- The page's server is tested through `WebApp.handle`, without a socket, and every protection has a test which shows it refusing.

## Documentation is part of the change

- **The docs are always in step with the code.** Update every affected page in the same change: the guides in `docs/guide`, the project pages, the README, and an "Unreleased" section in `docs/project/changelog.rst`.
- **Rewrite and reorganize as the code evolves**, so that the docs read as one coherent guide to what exists now. Do not append a section per change, and do not leave a description of how things used to be.
- Describe the design of this package in its own terms. Do not refer to other projects or sites which the setup, the structure or the look was modeled on; write the details down instead.
- The table of what each operation does is in `docs/guide/operations.rst` and in the README, and the page describes the operations in the same words; keep them equal.
- The diagrams in `docs/_static` are drawn by `docs/scripts/make_images.py`, in a light and a dark variant. Change `docs/scripts/_images/` and run `make docs-images`; do not edit the SVG files.
- The docs build with warnings as errors.

## Git and releases

- `master` is the main branch: changes go through a pull request, merged by squashing. The maintainer merges; do not merge yourself.
- Commit, push or open a pull request only when asked to.
- When the maintainer says a pull request is merged, clean up without being asked: switch to `master`, pull, delete the local branch of the pull request and, if it still exists, the one on `origin`, and prune the stale remote-tracking branches. Check that the pull request is merged before deleting; a squash merge needs `git branch -D`.
- The version is not written in any file. It is read from the git tag: `v0.1.0` gives `0.1.0`.
- To release: in a pull request, move the "Unreleased" section of `docs/project/changelog.rst` to the page of its minor version in `docs/project/changelog/`, under a heading with the version and its date. After it is merged, create a GitHub release on `master` with the tag `vX.Y.Z`. Publishing the release uploads to PyPI and pushes the image.
