import orjson
from pathlib import Path
from typing import Generic, TypeVar, AnyStr
from collections.abc import Mapping, Iterable, Iterator, Callable
from http import HTTPStatus
from multidict import CIMultiDict
from collections import deque
from wolf.http.datastructures import Cookies
from wolf.http.constants import EMPTY_STATUSES, REDIRECT_STATUSES
from wolf.http.types import HTTPCode


BodyT = str | bytes | Iterator[bytes]
HeadersT = Mapping[str, str] | Iterable[tuple[str, str]]
F = TypeVar("F", bound=Callable)


class Headers(CIMultiDict[str]):
    __slots__ = ("_cookies",)

    _cookies: Cookies

    def __new__(cls, *args, **kwargs):
        if not kwargs and len(args) == 1 and isinstance(args[0], cls):
            return args[0]
        inst = super().__new__(cls, *args, **kwargs)
        inst._cookies = None
        return inst

    @property
    def cookies(self) -> Cookies:
        if self._cookies is None:
            self._cookies = Cookies()
        return self._cookies

    def items(self):
        yield from super().items()
        if self._cookies:
            for cookie in self._cookies.values():
                yield "Set-Cookie", str(cookie)

    def coalesced_items(self) -> Iterable[tuple[str, str]]:
        """Coalescence of headers does NOT garanty order of headers.
        It garanties the order of the header values, though.
        """
        if self._cookies:
            cookies = (str(cookie) for cookie in self._cookies.values())
        else:
            cookies = None

        keys = frozenset(self.keys())
        for header in keys:
            values = self.getall(header)
            if header == "Set-Cookie" and cookies:
                values = [*values, *cookies]
            yield header, ", ".join(values)
        if "Set-Cookie" not in self and cookies:
            yield "Set-Cookie", ", ".join(cookies)


class FileResponse:

    __slots__ = ("status", "block_size", "headers", "filepath")

    def __init__(
        self,
        filepath: Path,
        status: HTTPCode = 200,
        block_size: int = 4096,
        headers: HeadersT | None = None,
    ):
        self.status = HTTPStatus(status)
        self.filepath = filepath
        self.headers = Headers(headers or ())  # idempotent.
        self.block_size = block_size


class Response(Generic[F]):
    __slots__ = ("status", "body", "headers", "_finishers")

    status: HTTPStatus
    headers: Headers
    body: BodyT | None
    _finishers: deque[F] | None

    def __init__(
        self,
        status: HTTPCode = 200,
        body: BodyT | None = None,
        headers: HeadersT | None = None,
    ):
        self.status = HTTPStatus(status)
        self.body = body
        self.headers = Headers(headers or ())  # idempotent.
        self._finishers = None

    def add_finisher(self, task: F):
        if self._finishers is None:
            self._finishers = deque([task])
        else:
            self._finishers.append(task)

    @property
    def cookies(self):
        return self.headers.cookies

    def __iter__(self) -> Iterator[bytes]:
        if self.status not in EMPTY_STATUSES:
            if self.body is None:
                yield self.status.description.encode()
            elif isinstance(self.body, bytes):
                yield self.body
            elif isinstance(self.body, str):
                yield self.body.encode()
            elif isinstance(self.body, Iterator):
                yield from self.body
            else:
                raise TypeError(f"Body of type {type(self.body)!r} is not supported.")

    @classmethod
    def to_json(
        cls,
        code: HTTPCode = 200,
        body: BodyT | None = None,
        headers: HeadersT | None = None,
    ) -> "Response":
        data = orjson.dumps(body)
        if headers is None:
            headers = {"Content-Type": "application/json"}
        else:
            headers = Headers(headers)
            headers["Content-Type"] = "application/json"
        return cls(code, data, headers)

    @classmethod
    def html(
        cls,
        code: HTTPCode = 200,
            body: AnyStr = b"",
            headers: HeadersT | None = None,
    ) -> "Response":
        if headers is None:
            headers = {"Content-Type": "text/html; charset=utf-8"}
        else:
            headers = Headers(headers)
            headers["Content-Type"] = "text/html; charset=utf-8"
        return cls(code, body, headers)

    @classmethod
    def redirect(
        cls,
        location,
        code: HTTPCode = 303,
        body: BodyT | None = None,
        headers: HeadersT | None = None,
    ) -> "Response":
        if code not in REDIRECT_STATUSES:
            raise ValueError(f"{code}: unknown redirection code.")
        if not headers:
            headers = {"Location": location}
        else:
            headers = Headers(headers)
            headers["Location"] = location
        return cls(code, body, headers)
