import typing as t
import urllib.parse
from contextlib import contextmanager
from pathlib import PurePosixPath
from wolf.utils import immutable_cached_property
from wolf.http.request import Request
from wolf.http.datastructures import Data
from wolf.http.headers import Cookies, ContentType, Languages, Accept
from wolf.http.headers.ranges import Ranges
from wolf.http.headers.utils import parse_host
from wolf.wsgi.types import WSGIEnviron
from wolf.wsgi.parsers import parser
from wolf.wsgi.response import WSGIResponse
from aioinject import Scoped, Object, SyncInjectionContext
from aioinject.extensions import SyncOnResolveExtension


T = t.TypeVar("T")
NONE_PROVIDED = object()
ACCEPT_ALL = Accept([])
ALL_LANGUAGES = Languages([])


class WSGIRequest(Request[WSGIEnviron], SyncOnResolveExtension):

    __slots__ = ('environ', 'context', 'response_cls')

    context: SyncInjectionContext | None
    response_cls: type[WSGIResponse]

    def __init__(
            self,
            environ: WSGIEnviron,
            response_cls: type[WSGIResponse] = WSGIResponse
    ):
        self.context = None
        self.environ = environ
        self.response_cls = response_cls

    @contextmanager
    def __call__(self, container) -> 'WSGIRequest':
        with container.sync_context() as context:
            context.register(Scoped(self.get_cookies))
            context.register(Scoped(self.get_query))
            context.register(Scoped(self.get_data))
            context.register(Object(self, type_=Request))
            self.context = context
            yield self
        self.context = None

    def get(self, t: type[T], *, default=NONE_PROVIDED):
        if self.context is None:
            raise NotImplementedError('Context is unavailable.')
        try:
            return self.context.resolve(t)
        except ValueError:
            if default is NONE_PROVIDED:
                raise
            return default

    @immutable_cached_property
    def method(self) -> str:
        return self.environ.get("REQUEST_METHOD", "GET").upper()

    @immutable_cached_property
    def body(self) -> t.BinaryIO:
        return self.environ["wsgi.input"]

    @immutable_cached_property
    def data(self) -> Data:
        if self.content_type:
            return parser.parse(
                self.environ["wsgi.input"],
                self.content_type
            )
        return Data()

    def get_data(self) -> Data:
        return self.data

    @immutable_cached_property
    def domain(self) -> str:
        domain, _ = self.host
        return domain

    @immutable_cached_property
    def accept(self) -> Accept:
        try:
            return Accept.from_string(
                self.environ["HTTP_ACCEPT"]
            )
        except KeyError:
            return ACCEPT_ALL

    @immutable_cached_property
    def range(self) -> Ranges | None:
        try:
            return Ranges.from_string(
                self.environ["RANGE"]
            )
        except KeyError:
            return None

    @immutable_cached_property
    def accept_language(self) -> Languages:
        try:
            return Languages.from_string(
                self.environ["HTTP_ACCEPT_LANGUAGE"]
            )
        except KeyError:
            return ALL_LANGUAGES

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
    def querystring(self) -> str:
        return self.environ.get("QUERY_STRING", "")

    @immutable_cached_property
    def cookies(self) -> Cookies:
        return Cookies.from_string(self.environ.get("HTTP_COOKIE", ""))

    @immutable_cached_property
    def content_type(self) -> ContentType | None:
        try:
            return ContentType.from_string(self.environ["CONTENT_TYPE"])
        except KeyError:
            return None

    @immutable_cached_property
    def scheme(self) -> str:
        return self.environ.get("wsgi.url_scheme", "http")

    @immutable_cached_property
    def host(self) -> tuple[str, int]:
        try:
            domain, port = parse_host(self.environ["HTTP_HOST"])
        except KeyError:
            domain = self.environ["SERVER_NAME"]
            port = self.environ.get("SERVER_PORT", None)
            if port is None:
                port = 80 if self.scheme == "http" else 443
        return domain, port
