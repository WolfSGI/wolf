import typing as t
from kettu.http.headers.utils import parse_list_header, parse_host
from wolf.wsgi.app import WSGIApplication
from wolf.wsgi.types import WSGIEnviron, StartResponse


class ProxyMiddleware:

    def __init__(
        self,
        app: WSGIApplication,
        x_for: int = 1,
        x_proto: int = 1,
        x_host: int = 1,
        x_port: int = 1,
        x_prefix: int = 1,
    ) -> None:
        self.app = app
        self.x_for = x_for
        self.x_proto = x_proto
        self.x_host = x_host
        self.x_port = x_port
        self.x_prefix = x_prefix

    def get_value(self, trusted: int, value: str | None) -> str | None:
        if not (trusted and value):
            return None
        values = parse_list_header(value)
        if len(values) >= trusted:
            return values[-trusted]
        return None

    def __call__(
        self, environ: WSGIEnviron, start_response: StartResponse
    ) -> t.Iterable[bytes]:

        orig_remote_addr = environ.get("REMOTE_ADDR")
        orig_wsgi_url_scheme = environ.get("wsgi.url_scheme")
        orig_http_host = environ.get("HTTP_HOST")
        environ.update(
            {
                "proxymiddleware.canonical": {
                    "REMOTE_ADDR": orig_remote_addr,
                    "wsgi.url_scheme": orig_wsgi_url_scheme,
                    "HTTP_HOST": orig_http_host,
                    "SERVER_NAME": environ.get("SERVER_NAME"),
                    "SERVER_PORT": environ.get("SERVER_PORT"),
                    "SCRIPT_NAME": environ.get("SCRIPT_NAME"),
                }
            }
        )

        x_for = self.get_value(self.x_for, environ.get("HTTP_X_FORWARDED_FOR"))
        if x_for:
            environ["REMOTE_ADDR"] = x_for

        x_proto = self.get_value(
            self.x_proto, environ.get("HTTP_X_FORWARDED_PROTO")
        )
        if x_proto:
            environ["wsgi.url_scheme"] = x_proto

        x_host = self.get_value(
            self.x_host, environ.get("HTTP_X_FORWARDED_HOST"))
        if x_host:
            environ["HTTP_HOST"] = environ["SERVER_NAME"] = x_host
            environ["SERVER_NAME"], environ["SERVER_PORT"] = (
                parse_host(x_host))

        x_port = self.get_value(
            self.x_port, environ.get("HTTP_X_FORWARDED_PORT"))
        if x_port:
            host = environ.get("HTTP_HOST")
            if host:
                host, port = parse_host(host)
                environ["HTTP_HOST"] = f"{host}:{x_port}"
            environ["SERVER_PORT"] = x_port

        x_prefix = self.get_value(
            self.x_prefix, environ.get("HTTP_X_FORWARDED_PREFIX")
        )
        if x_prefix:
            environ["SCRIPT_NAME"] = x_prefix

        return self.app(environ, start_response)
