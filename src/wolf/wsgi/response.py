from typing import Iterable
from pathlib import Path
from http import HTTPStatus
from wolf.http.response import Response, HeadersT, Headers
from wolf.http.types import HTTPCode
from wolf.wsgi.types import WSGIEnviron, WSGICallable, StartResponse, Finisher


class WSGIResponse(WSGICallable, Response[Finisher]):
    def close(self):
        """Exhaust the list of finishers. No error is handled here.
        An exception will cause the closing operation to fail during iteration.
        """
        if self._finishers:
            while self._finishers:
                finisher = self._finishers.popleft()
                finisher(self)

    def __call__(
        self, environ: WSGIEnviron, start_response: StartResponse
    ) -> Iterable[bytes]:
        status = f"{self.status.value} {self.status.phrase}"
        start_response(status, list(self.headers.items()))
        return self


class FileWrapperResponse(WSGICallable):
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

    def __call__(self, environ: WSGIEnviron, start_response: StartResponse):
        status = f"{self.status.value} {self.status.phrase}"
        start_response(status, list(self.headers.items()))
        filelike = self.filepath.open("rb")
        return environ["wsgi.file_wrapper"](filelike, self.block_size)
