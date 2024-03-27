from typing import Any
from types import TracebackType
from collections.abc import Mapping, Sequence, Iterable, Callable
from wolf.http.response import Response
from wolf.http.types import StatusCode


WSGIEnviron = Mapping[str, Any]
ExceptionInfo = (
    tuple[type[BaseException], BaseException, TracebackType] |
    tuple[None, None, None] |
    None
)
ResponseHeaders = Sequence[tuple[str | bytes, str | bytes]]
StartResponse = Callable[
    [StatusCode, ResponseHeaders, ExceptionInfo],
    Callable[[bytes], None] | None,
]
WSGICallable = Callable[[WSGIEnviron, StartResponse], Iterable[bytes]]
Finisher = Callable[[Response], None]
