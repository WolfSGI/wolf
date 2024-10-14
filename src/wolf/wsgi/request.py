import typing as t
import urllib.parse
from datetime import datetime
from contextlib import contextmanager
from kettu.utils import immutable_cached_property
from kettu.http.request import Request, header_property
from kettu.http.datastructures import Data
from kettu.http.headers import Cookies, ContentType, Languages, Accept, ETag, ETags
from kettu.http.headers import Ranges
from kettu.http.headers.utils import parse_host, parse_http_datetime, parse_wsgi_path
from wolf.wsgi.types import WSGIEnviron
from wolf.wsgi.parsers import parser
from wolf.wsgi.response import WSGIResponse
from aioinject import Scoped, Object, SyncInjectionContext
from aioinject.extensions import SyncOnResolveExtension


T = t.TypeVar("T")
NONE_PROVIDED = object()
ACCEPT_ALL = Accept([])
ALL_LANGUAGES = Languages([])
ALL_ETAGS = ETags([])


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
            context.register(Object(self, type_=WSGIRequest))
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

    path: str = header_property(
        "PATH_INFO",
        caster=parse_wsgi_path,
        default="/"
    )

    root_path: str = header_property(
        "SCRIPT_NAME",
        default="",
        caster=urllib.parse.quote
    )

    cookies: Cookies | None = header_property(
        "HTTP_COOKIE",
        caster=Cookies.from_string,
        default=None
    )

    scheme: str = header_property(
        "wsgi.url_scheme",
        default="http"
    )

    querystring: str = header_property(
        "QUERY_STRING",
        default=""
    )

    content_type: ContentType | None = header_property(
        "CONTENT_TYPE",
        caster=ContentType.from_string,
        default=None
    )

    content_length: int | None = header_property(
        "CONTENT_LENGTH",
        caster=int,
        default=None
    )

    method: str = header_property(
        "REQUEST_METHOD",
        default="GET"
    )

    body: t.BinaryIO = header_property(
        "wsgi.input"
    )

    remote_addr: str = header_property(
        "REMOTE_ADDR",
        default="127.0.0.1"
    )

    accept: Accept = header_property(
        "HTTP_ACCEPT",
        caster=Accept.from_string,
        default=ACCEPT_ALL
    )

    accept_language: Languages = header_property(
        "HTTP_ACCEPT_LANGUAGE",
        caster=Languages.from_string,
        default=ALL_LANGUAGES
    )

    range: Ranges | None = header_property(
        "HTTP_RANGE",
        caster=Ranges.from_string
    )

    if_match: ETags = header_property(
        "HTTP_IF_MATCH",
        default=ALL_ETAGS
    )

    if_none_match: ETags = header_property(
        "HTTP_IF_NONE_MATCH",
        default=ALL_ETAGS
    )

    if_modified_since: datetime | None = header_property(
        "HTTP_IF_MODIFIED_SINCE",
        caster=parse_http_datetime,
        default=None
    )

    if_unmodified_since: datetime | None = header_property(
        "HTTP_IF_UNMODIFIED_SINCE",
        caster=parse_http_datetime,
        default=None
    )

    @immutable_cached_property
    def if_range(self) -> ETag | datetime | None:
        try:
            value = self.environ["HTTP_IF_RANGE"]
            if '"' in value:
                return ETag.from_string(value)
            return parse_http_datetime(value)
        except KeyError:
            return None

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

    @immutable_cached_property
    def domain(self) -> str:
        domain, _ = self.host
        return domain

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
