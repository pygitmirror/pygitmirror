"""Serving the web application over HTTP."""

import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pygitmirror.web import _security
from pygitmirror.web.request import Request
from pygitmirror.web.web_app import WebApp

_logger = logging.getLogger(__name__)

#: The port of the page. An unusual one, so that it does not take a port
#: which a development server on the same machine expects to be free.
DEFAULT_PORT = 47417


def _handler(app: WebApp) -> type[BaseHTTPRequestHandler]:
    """Create the class which passes the requests of a server to an application."""

    class Handler(BaseHTTPRequestHandler):
        server_version = "git-mirror"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def _answer(self) -> None:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length < 0 or length > _security.MAX_BODY:
                self.send_error(413)
                return
            headers = {name.lower(): value for name, value in self.headers.items()}
            request = Request(self.command, self.path, headers, self.rfile.read(length))
            response = app.handle(request)
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            for name, value in response.headers.items():
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(response.body)

        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _answer  # noqa: N815

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            # The first line of a request may hold the access key.
            _logger.debug("%s %s", self.address_string(), self.path.split("?", 1)[0])

    return Handler


def make_server(
    app: WebApp, host: str = "127.0.0.1", port: int = DEFAULT_PORT
) -> ThreadingHTTPServer:
    """Create the HTTP server of an application, without starting it.

    :param app: the application
    :param host: the address to listen on; that of the local machine only
        by default
    :param port: the port to listen on, 0 for a free one
    :returns: the server; call ``serve_forever()`` to run it
    """
    server = ThreadingHTTPServer((host, port), _handler(app))
    server.daemon_threads = True
    return server


def serve(app: WebApp, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
    """Run the application until it is interrupted.

    The link to the page, with the access key, is logged once.

    :param app: the application
    :param host: the address to listen on
    :param port: the port to listen on
    """
    server = make_server(app, host, port)
    shown = "127.0.0.1" if host in ("0.0.0.0", "::") else host  # noqa: S104
    _logger.warning(
        "git-mirror is running. Open http://%s:%d/?key=%s", shown, server.server_port, app.key
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
