import svcs
import typing as t
import urllib.parse
from contextlib import contextmanager
from datetime import datetime
from svcs.exceptions import ServiceNotFoundError

from kettu.datastructures import Data
from kettu.exceptions import HTTPError
from kettu import headers

from typing import TypeVar, Generic, Any
from wolf.utils import immutable_cached_property
from wolf.abc.request import RequestProtocol
from wolf.wsgi.parsers import parser
from wolf.wsgi.response import Response, FileWrapperResponse
from wolf.wsgi.types import WSGIEnviron


T = t.TypeVar("T")

NONE_PROVIDED = object()
ACCEPT_ALL = headers.Accept([])
ALL_LANGUAGES = headers.Languages([])
ALL_ETAGS = headers.ETags([])

UNSET = object()


def header_property(
        name: str,
        *,
        caster=None,
        default=UNSET,
        on_missing: int = 400
):
    """Create a read-only cached header property.
    """
    def getter(request: RequestProtocol):
        try:
            value = request.environ[name]
            if caster is not None:
                value = caster(value)
        except KeyError:
            if default is UNSET:
                raise HTTPError(on_missing)
            value = default
        return value

    return immutable_cached_property(getter)


class Request(RequestProtocol[WSGIEnviron]):

    __slots__ = ('environ', 'context', 'response_cls')

    context: svcs.Container | None
    response_cls: type[Response] | type[FileWrapperResponse]

    def __init__(
            self,
            environ: WSGIEnviron,
            response_cls: type[Response] | type[FileWrapperResponse] = Response
    ):
        self.context = None
        self.environ = environ
        self.response_cls = response_cls

    @contextmanager
    def __call__(self, registry: svcs.Registry) -> 'Request':
        with svcs.Container(registry) as context:
            context.register_local_factory(
                headers.Cookies, lambda: self.cookies)
            context.register_local_factory(
                headers.Query, lambda: self.query)
            context.register_local_factory(Data, lambda: self.data)
            context.register_local_value(Request, self)
            self.context = context
            yield self
        self.context = None

    def get(self, t: type[T], *, default=NONE_PROVIDED):
        if self.context is None:
            raise NotImplementedError('Context is unavailable.')
        try:
            return self.context.get(t)
        except ServiceNotFoundError:
            if default is NONE_PROVIDED:
                raise
            return default

    path: str = header_property(
        "PATH_INFO",
        caster=headers.parse_wsgi_path,
        default="/"
    )

    root_path: str = header_property(
        "SCRIPT_NAME",
        default="",
        caster=urllib.parse.quote
    )

    cookies: headers.Cookies | None = header_property(
        "HTTP_COOKIE",
        caster=headers.Cookies.from_string,
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

    content_type: headers.ContentType | None = header_property(
        "CONTENT_TYPE",
        caster=headers.ContentType.from_string,
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

    accept: headers.Accept = header_property(
        "HTTP_ACCEPT",
        caster=headers.Accept.from_string,
        default=ACCEPT_ALL
    )

    accept_language: headers.Languages = header_property(
        "HTTP_ACCEPT_LANGUAGE",
        caster=headers.Languages.from_string,
        default=ALL_LANGUAGES
    )

    range: headers.Ranges | None = header_property(
        "HTTP_RANGE",
        caster=headers.Ranges.from_string
    )

    if_match: headers.ETags = header_property(
        "HTTP_IF_MATCH",
        default=ALL_ETAGS
    )

    if_none_match: headers.ETags = header_property(
        "HTTP_IF_NONE_MATCH",
        default=ALL_ETAGS
    )

    if_modified_since: datetime | None = header_property(
        "HTTP_IF_MODIFIED_SINCE",
        caster=headers.parse_http_datetime,
        default=None
    )

    if_unmodified_since: datetime | None = header_property(
        "HTTP_IF_UNMODIFIED_SINCE",
        caster=headers.parse_http_datetime,
        default=None
    )

    @immutable_cached_property
    def if_range(self) -> headers.ETag | datetime | None:
        try:
            value = self.environ["HTTP_IF_RANGE"]
            if '"' in value:
                return ETag.from_string(value)
            return headers.parse_http_datetime(value)
        except KeyError:
            return None

    @immutable_cached_property
    def host(self) -> tuple[str, int]:
        try:
            domain, port = headers.parse_host(self.environ["HTTP_HOST"])
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
