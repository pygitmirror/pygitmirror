import re

import pytest

from pygitmirror.web._static import FILES
from tests.web.conftest import Client

PAGES = [name for name in FILES if name.endswith(".html")]


def test_files_are_served_with_their_type(client: Client) -> None:
    css = client.get("/static/tokens.css", key=False)
    assert css.status == 200 and css.content_type.startswith("text/css")
    assert client.get("/static/app.js").content_type.startswith("text/javascript")
    font = client.get("/static/ibm-plex-mono-latin-400-normal.woff2")
    assert font.content_type == "font/woff2" and font.body[:4] == b"wOF2"


@pytest.mark.parametrize(
    "name", ["../web_app.py", "..%2Fweb_app.py", "missing.css", "", "sub/app.js", "/etc/passwd"]
)
def test_only_the_files_of_the_page_are_served(client: Client, name: str) -> None:
    assert client.get(f"/static/{name}").status == 404


@pytest.mark.parametrize("page", PAGES)
def test_pages_refer_to_files_which_exist(page: str) -> None:
    text = FILES[page][0].decode()
    referred = re.findall(r'(?:href|src)="/static/([^"]+)"', text)
    assert referred and all(name in FILES for name in referred)


@pytest.mark.parametrize("page", PAGES)
def test_pages_have_nothing_the_content_policy_forbids(page: str) -> None:
    text = FILES[page][0].decode()
    assert " style=" not in text and "<style" not in text
    assert not re.search(r"<script(?![^>]*\bsrc=)", text)
    assert not re.search(r"\son[a-z]+=", text)
    assert "http://" not in text.replace("http://localhost", "") and "https://" not in text


def test_scripts_and_styles_load_nothing_from_elsewhere() -> None:
    for name, (content, _) in FILES.items():
        if name.endswith((".js", ".css")):
            text = content.decode()
            # Addresses appear as examples in fields, never as something to load.
            for loading in ("url(http", 'from "http', 'import("http', 'fetch("http', "//cdn"):
                assert loading not in text, (name, loading)
            assert "innerHTML" not in text and "eval(" not in text, name


def test_modules_import_files_which_exist() -> None:
    for name, (content, _) in FILES.items():
        if name.endswith(".js"):
            for imported in re.findall(r'from "\./([^"]+)"', content.decode()):
                assert imported in FILES, (name, imported)


def test_the_font_license_is_shipped() -> None:
    assert b"SIL Open Font License" in FILES["OFL.txt"][0]
