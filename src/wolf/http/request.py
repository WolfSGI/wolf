import urllib.parse
from typing import TypeVar, Generic
from abc import ABC, abstractmethod
from collections.abc import Mapping
from wolf.utils import immutable_cached_property
from wolf.http.response import Response
from wolf.http.headers import Query, Cookies, ContentType
from aioinject.context import SyncInjectionContext, InjectionContext


E = TypeVar("E", bound=Mapping)


class Request(ABC, Generic[E]):
    environ: E
    response_cls: type[Response]
    context: SyncInjectionContext | InjectionContext

    @property
    @abstractmethod
    def method(self) -> str: ...

    @property
    @abstractmethod
    def domain(self) -> str: ...

    @property
    @abstractmethod
    def root_path(self) -> str: ...

    @property
    @abstractmethod
    def path(self) -> str: ...

    @property
    @abstractmethod
    def querystring(self) -> str | bytes: ...

    @property
    @abstractmethod
    def cookies(self) -> Cookies: ...

    def get_cookies(self) -> Cookies:
        return self.cookies

    @property
    @abstractmethod
    def content_type(self) -> ContentType: ...

    @property
    @abstractmethod
    def host(self) -> tuple[str | None, int | None]:
        ...

    @property
    @abstractmethod
    def scheme(self) -> str: ...

    @immutable_cached_property
    def query(self) -> Query:
        return Query.from_string(self.querystring)

    def get_query(self) -> Query:
        return self.query

    @immutable_cached_property
    def application_uri(self) -> str:
        scheme = self.scheme
        server, port = self.host
        if not port:
            port = (scheme == 'https' and 443 or 80)

        if (self.scheme == "http" and port == 80) or (
            self.scheme == "https" and port == 443
        ):
            return f"{scheme}://{server}{self.root_path}"
        return f"{scheme}://{server}:{port}{self.root_path}"

    def uri(self, include_query: bool = True) -> str:
        path_info = urllib.parse.quote(self.path)
        if include_query:
            qs = urllib.parse.quote(self.querystring)
            if qs:
                return f"{self.application_uri}{path_info}?{qs}"
        return f"{self.application_uri}{path_info}"


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
    def getter(request: Request):
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
