from typing import Literal
from http import HTTPStatus
from collections.abc import Sequence


HTTPMethod = Literal["GET", "HEAD", "PUT", "DELETE", "PATCH", "POST", "OPTIONS"]
HTTPMethods = Sequence[HTTPMethod]

Boundary = str | bytes
Charset = str | bytes
MIMEType = str | bytes
HTTPCode = HTTPStatus | int
StatusCode = str | bytes
