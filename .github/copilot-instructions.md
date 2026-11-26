# Instructions for coding agents

`pygitmirror` clones, syncs and migrates git repositories between GitHub, GitLab, Gitea, Bitbucket and plain git servers. It is the `git-mirror` command and a Python library. It runs the git executable, calls the APIs of the hosts with the standard library, and has no dependencies; it is meant to stay that way.

A web version, in which users connect their accounts and clone, sync or migrate between the four services, will be built on the library. Keep the library usable by it: no global state, no input from a terminal, results as objects.

## Where knowledge lives

Everything a contributor needs to know is in this repository. Keep it there: do not store rules, plans or decisions in a memory or notes of your own.

| When you | Read | And update it when |
| --- | --- | --- |
| start any work | this file | you are given a rule which should hold from now on |
| change how the parts work together, or add a host | `docs/project/design.rst` | the structure or the steps of an operation change |
| look for what to do, or put something off | `docs/project/roadmap.rst` | work is finished, found or postponed |
| are about to choose between alternatives | `docs/project/decisions.rst` | a choice is made which someone could later question |
| work on a host, on git commands or on a workflow | `docs/project/maintenance.rst` | you learn something the next person would have to learn again, or verify a host against the real service |

Do not reopen a decision recorded in `docs/project/decisions.rst` without a new reason; say what changed. Update these files in the same change as the work they describe.

## Commands

Everything runs through `uv` and the top-level `Makefile`. Do not add another task runner or per-folder make files. All dependencies, those of the docs included, are dependency groups in `pyproject.toml`; do not add requirements files.

```shell
make install   # create the environment from uv.lock
make check     # lint, type check, test and build the docs: run it before you finish
make format    # format and apply the safe lint fixes
make           # list all targets
```

The workflows in `.github/workflows` call make targets only. A step which needs more than one command is a Python script in `.github/scripts` with a make target of its own, not shell in the workflow.

## The design in brief

`docs/project/design.rst` is the full description. What must hold:

- **Three layers, one direction.** `git` knows git and no host. `hosts` knows the services and no git. `mirror` combines them into the operations. `config` and `cli` are one user of the library and are imported by nothing else.
- **One sequence of steps for all operations**, in `mirror/_transfer.py`: list both ends, create the destination if missing, plan, fetch, check, push, set the default branch, delete, verify, archive. Clone, sync and migrate differ only in whether they overwrite, delete, verify and archive.
- **The order of the steps keeps a failure harmless**: nothing is deleted before everything was added, and the source is archived only after the copy was verified. A failed operation can be run again.
- **The local mirror equals the source** after a fetch, holds branches and tags only, and stores no address or credential.
- **A host is one class** derived from `Host`, registered in `hosts/_factory.py`. Operations must not test for a particular provider; they ask the host (`has_api`, `can_archive`).

## Rules for the code

- **American English** in code, comments, documentation and commit messages: color, behavior, modeling, analyze.
- **One public class per module**, named after it in snake case. Modules of helper functions without a public class start with an underscore, such as `_transfer.py`. Exceptions share `errors.py`.
- **Files stay under 300 lines**; a test checks it. Split a file before it reaches that size, into a private module or subpackage next to it.
- **Standard tooling only.** `ruff` for lint and format, `mypy` in strict mode, `pytest`. No unusual configuration.
- Every public module, class, method and function has a docstring with Sphinx field lists (`:param name:`, `:returns:`, `:raises Error:`). Types are in the hints, not in the docstrings.
- Mark an overriding method with `override` from `pygitmirror._compat`, which supports Python 3.11; it inherits the docstring.
- Errors which the package reports derive from `GitMirrorError`.

## Tokens must not leak

This is the promise of the package which is easiest to break.

- Never put a token in a URL or in an argument of a command. A host gives git its token through `Host.git_config()`, which `Git` passes in the environment of the command.
- The API client sends its headers to one server only. Do not follow a redirect or a link to another one.
- Pass what is logged or put into an error through `redact()`. Do not log headers or the environment.
- The command reads tokens from environment variables only: no option and no key of the settings file for a token.
- The library takes a token as an argument and never reads the environment.

## Input is not trusted

Repository names and addresses will come from users of a web page.

- Build a repository name with `RepositoryRef`, which rejects what could leave a folder or be read as an option. Do not build paths or URLs from raw strings.
- Run git through `Git` only, never through a shell. It limits the transports and never waits for input.

## Destructive behavior is opt-in

- `clone` and `migrate` never overwrite or delete at the destination. Only `sync` does.
- Only `migrate` with `archive_source` changes the source, and nothing ever deletes a repository.
- A new step which changes a host must be skipped in a dry run.
- A repository whose visibility is unknown is created private.

## Tests

- git is real in the tests: they create repositories in a temporary folder and run git on them (`Workshop` in `tests/helpers.py`). Do not replace git with a stand-in.
- The APIs are stand-ins: `FakeTransport` answers requests from a table, `FolderHost` is a host with an API on folders. The tests need no network and no account.
- A change to a host is also tried against the real service when possible. Record in `docs/project/maintenance.rst` what was verified, and never claim there what was not tried.

## Documentation is part of the change

- Update every affected page in the same change: the guide pages in `docs/guide`, the README, and an "Unreleased" section in `docs/project/changelog.rst`, above the list of versions.
- Rewrite and reorganize so that the docs read as one coherent guide. Do not append a section per change.
- The table of what each operation does is in `docs/guide/operations.rst` and in the README; keep them equal.
- The docs build with warnings as errors.

## Git and releases

- `master` is the main branch: changes go through a pull request, merged by squashing. The maintainer merges; do not merge yourself.
- Commit, push or open a pull request only when asked to.
- The version is not written in any file. It is read from the git tag: `v0.1.0` gives `0.1.0`.
- To release: in a pull request, move the "Unreleased" section of `docs/project/changelog.rst` to the page of its minor version in `docs/project/changelog/`, under a heading with the version and its date. After it is merged, create a GitHub release on `master` with the tag `vX.Y.Z`. Publishing the release uploads to PyPI.
