import typing as t
from types import TracebackType
from sleigh.http.types import StatusCode


WSGIEnviron = t.Mapping[str, t.Any]
ExceptionInfo = t.Union[
    t.Tuple[t.Type[BaseException], BaseException, TracebackType],
    t.Tuple[None, None, None]
]
ResponseHeaders = t.Iterable[t.Tuple[str, str]]
StartResponse = t.Callable[
    [StatusCode, ResponseHeaders, t.Optional[ExceptionInfo]],
    t.Optional[t.Callable[[t.ByteString], None]]
]
WSGICallable = t.Callable[[WSGIEnviron, StartResponse], t.Iterable[bytes]]
Finisher = t.Callable[['Response'], None]
