"""Sphinx configuration for the pygitmirror documentation."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version

from packaging.version import Version

# -- Project information ------------------------------------------------------

project = "pygitmirror"
author = "Bassem Girgis"
copyright = "2024-2026 Bassem Girgis"

try:
    _installed = Version(_dist_version("pygitmirror"))
except PackageNotFoundError as exc:  # pragma: no cover
    raise RuntimeError(
        "pygitmirror must be installed to build the documentation; run `make install` first."
    ) from exc

# The package version is derived from the git tags. A build of a release tag
# shows that version. Any other build, such as the one of the main branch, is
# labeled as the development version instead of the derived version (for
# example 0.4.1.dev3+g1a2b3c4), which reads like a release which does not
# exist.
if _installed.is_devrelease or _installed.local:
    release = "dev"
    version = "dev"
    _title_version = "(development version)"
else:
    release = str(_installed)
    version = f"{_installed.major}.{_installed.minor}"
    _title_version = release

# -- General configuration ----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

source_suffix = {".rst": "restructuredtext"}
master_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Report every broken cross-reference.
nitpicky = True

autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Generate the API reference pages from the autosummary directives.
autosummary_generate = True
# Document the public names a package exports through ``__all__``.
autosummary_ignore_module_all = False
templates_path = ["_layouts"]

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# -- References to the package's own names ------------------------------------


def _resolve_own_names(app, env, node, contnode):  # type: ignore[no-untyped-def]
    """Resolve the references which name an object where it is defined.

    The reference documents an object where it is exported, such as
    ``pygitmirror.hosts.Host``, while docstrings and type hints name it by
    the module which defines it, ``pygitmirror.hosts.host.Host``. Errors are
    named without their module in ``:raises:`` fields.
    """
    target = node.get("reftarget", "")
    parts = target.split(".")
    candidates = [f"pygitmirror.errors.{target}"] if len(parts) == 1 else []
    candidates += [".".join(parts[:i] + parts[i + 1 :]) for i in range(1, len(parts))]
    domain = env.get_domain("py")
    for name in candidates:
        if name in domain.objects:
            return domain.resolve_xref(
                env, node["refdoc"], app.builder, node.get("reftype"), name, node, contnode
            )
    return None


def setup(app):  # type: ignore[no-untyped-def]
    """Register the hooks of this configuration."""
    app.connect("missing-reference", _resolve_own_names)


# -- Options for HTML output --------------------------------------------------

# Furo follows the system color scheme and lets the reader switch between the
# light and dark themes.
html_theme = "furo"
html_title = f"pygitmirror {_title_version}"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/pygitmirror/pygitmirror/",
    "source_branch": "master",
    "source_directory": "docs/",
}
pygments_style = "default"
pygments_dark_style = "monokai"
