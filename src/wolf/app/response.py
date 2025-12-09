from typing import Iterable
from wolf.abc.response import ResponseProtocol, FileResponseProtocol
from wolf.app.types import WSGIEnviron, WSGICallable, StartResponse, Finisher


class Response(WSGICallable, ResponseProtocol[Finisher]):

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


class FileWrapperResponse(WSGICallable, FileResponseProtocol):

    def __call__(self, environ: WSGIEnviron, start_response: StartResponse):
        status = f"{self.status.value} {self.status.phrase}"
        start_response(status, list(self.headers.items()))
        filelike = self.filepath.open("rb")
        return environ["wsgi.file_wrapper"](filelike, self.block_size)
