from http import HTTPStatus
from wolf.http.types import HTTPCode


class ParsingException(ValueError):
    pass


class HTTPError(Exception):
    def __init__(self, status: HTTPCode, body: str | bytes | None = None):
        self.status = HTTPStatus(status)
        body = self.status.description if body is None else body
        if isinstance(body, str):
            body = body.encode("utf-8")
        elif not isinstance(body, bytes):
            raise ValueError("Body must be string or bytes.")
        self.body: bytes = body
