import typing as t
import urllib.parse
from pathlib import PurePosixPath
from wolf.utils import immutable_cached_property
from wolf.http.request import Request
from wolf.http.datastructures import Data, Cookies, ContentType, Query
from wolf.wsgi.types import WSGIEnviron
from wolf.wsgi.parsers import parser
from wolf.wsgi.response import WSGIResponse
from aioinject import Scoped, Object, SyncInjectionContext, Provider
from aioinject.extensions import SyncOnResolveExtension


T = t.TypeVar("T")
NONE_PROVIDED = object()


class WSGIRequest(Request[WSGIEnviron], SyncOnResolveExtension):
    context: SyncInjectionContext | None = None
    provides: set[type]
    response_cls: t.ClassVar[type[WSGIResponse]] = WSGIResponse

    def __init__(self, environ: WSGIEnviron):
        self.environ = environ
        self.provides = set()

    def on_resolve(
        self, context: SyncInjectionContext, provider: Provider[T], instance: T
    ) -> None:
        self.provides.add(provider.type_)

    def get(self, t: type[T], *, default=NONE_PROVIDED):
        try:
            return self.context.resolve(t)
        except ValueError:
            if default is NONE_PROVIDED:
                raise
            return default

    def set_context(self, context: SyncInjectionContext):
        context.register(Scoped(self.get_cookies))
        context.register(Scoped(self.get_query))
        context.register(Scoped(self.get_data))
        context.register(Object(self, type_=Request))
        self.context = context

    @immutable_cached_property
    def method(self) -> str:
        return self.environ.get("REQUEST_METHOD", "GET").upper()

    @immutable_cached_property
    def body(self) -> t.BinaryIO:
        return self.environ["wsgi.input"]

    @immutable_cached_property
    def data(self) -> Data:
        if self.content_type:
            return parser.parse(self.environ["wsgi.input"], self.content_type)
        return Data()

    def get_data(self) -> Data:
        return self.data

    @immutable_cached_property
    def domain(self) -> str:
        return self.environ["HTTP_HOST"].split(":", 1)[0]

    @immutable_cached_property
    def root_path(self) -> str:
        return urllib.parse.quote(self.environ.get("SCRIPT_NAME", ""))

    @immutable_cached_property
    def path(self) -> str:
        # according to PEP 3333 the native string representing PATH_INFO
        # (and others) can only contain unicode codepoints from 0 to 255,
        # which is why we need to decode to latin-1 instead of utf-8 here.
        # We transform it back to UTF-8
        # Note that it's valid for WSGI server to omit the value if it's
        # empty.
        if path := self.environ.get("PATH_INFO"):
            # Normalize the slashes to avoid things like '//test'
            return str(PurePosixPath(path.encode("latin-1").decode("utf-8")))
        return "/"

    @immutable_cached_property
    def querystring(self) -> Query:
        return self.environ.get("QUERY_STRING", "")

    @immutable_cached_property
    def cookies(self) -> Cookies:
        return Cookies.from_string(self.environ.get("HTTP_COOKIE", ""))

    @immutable_cached_property
    def content_type(self) -> ContentType:
        return ContentType(self.environ.get("CONTENT_TYPE", ""))

    @immutable_cached_property
    def scheme(self) -> str:
        return self.environ.get("wsgi.url_scheme", "http")

    @immutable_cached_property
    def host(self) -> str:
        http_host = self.environ.get("HTTP_HOST")
        if not http_host:
            server = self.environ["SERVER_NAME"]
            port = self.environ.get("SERVER_PORT", None)
            if port is None:
                port = 80 if self.scheme == "http" else 443
            http_host = f"{server}:{port}"
        return http_host
