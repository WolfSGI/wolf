import typing as t
from http import HTTPStatus


HTTPMethod = t.Literal["GET", "HEAD", "PUT", "DELETE", "PATCH", "POST", "OPTIONS"]
HTTPMethods = t.Iterable[HTTPMethod]

Boundary = str | bytes
Charset = str | bytes
MIMEType = str | bytes
HTTPCode = HTTPStatus | int
StatusCode = str | bytes
