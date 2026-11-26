# Contributing to pygitmirror

Bug reports, feature requests and pull requests are welcome, in particular for further hosts.

## Reporting a problem

Open an issue at https://github.com/pygitmirror/pygitmirror/issues with:

- the versions of `pygitmirror`, Python and git
- the services of the source and the destination
- the command and its output with `--log DEBUG`, with tokens and private addresses removed
- what you expected and what happened instead

Report a vulnerability privately instead, as [SECURITY.md](SECURITY.md) describes.

## Making a change

```shell
git clone https://github.com/pygitmirror/pygitmirror.git
cd pygitmirror
make install  # create the environment with uv
make check    # lint, type check, test and build the docs
```

Run `make` to list all targets. A pull request should:

- keep `make check` passing
- add tests for the change; a fix comes with a test which fails without it
- test with real git repositories on disk where git is involved, as the existing tests do
- keep tokens out of files, URLs, command lines and logs
- say which real services a change to a host was tried against
- update the documentation in the same pull request, with an "Unreleased" entry in `docs/project/changelog.rst`
- put every new class in its own module, and keep every file under 300 lines

The [design page](https://pygitmirror.readthedocs.io/en/latest/project/design.html) describes how the package is built and how to add a host, and the [development page](https://pygitmirror.readthedocs.io/en/latest/project/development.html) the layout, the code style and the tests.

## License

By contributing you agree that your contribution is released under the MIT license of the project.
