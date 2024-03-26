from dataclasses import dataclass
from typing import Optional, Iterable, Tuple, Iterator
from wolf.http.types import HTTPMethod


Header = Tuple[str, str]
Headers = Iterator[Header]


@dataclass
class CORSPolicy:
    origin: str = "*"
    methods: Optional[Iterable[HTTPMethod]] = None
    allow_headers: Optional[Iterable[str]] = None
    expose_headers: Optional[Iterable[str]] = None
    credentials: Optional[bool] = None
    max_age: Optional[int] = None

    def headers(self) -> Headers:
        yield "Access-Control-Allow-Origin", self.origin
        if self.methods is not None:
            values = ", ".join(self.methods)
            yield "Access-Control-Allow-Methods", values
        if self.allow_headers is not None:
            values = ", ".join(self.allow_headers)
            yield "Access-Control-Allow-Headers", values
        if self.expose_headers is not None:
            values = ", ".join(self.expose_headers)
            yield "Access-Control-Expose-Headers", values
        if self.max_age is not None:
            yield "Access-Control-Max-Age", str(self.max_age)
        if self.credentials:
            yield "Access-Control-Allow-Credentials", "true"

    def preflight(
        self,
        origin: Optional[str] = None,
        acr_method: Optional[str] = None,
        acr_headers: Optional[str] = None,
    ) -> Headers:
        if origin:
            if self.origin == "*":
                yield "Access-Control-Allow-Origin", "*"
            elif origin == self.origin:
                yield "Access-Control-Allow-Origin", origin
                yield "Vary", "Origin"
            else:
                yield "Access-Control-Allow-Origin", self.origin
                yield "Vary", "Origin"

        if self.methods is not None:
            yield "Access-Control-Allow-Methods", ", ".join(self.methods)
        elif acr_method:
            yield "Access-Control-Allow-Methods", acr_method

        if self.allow_headers is not None:
            values = ", ".join(self.allow_headers)
            yield "Access-Control-Allow-Headers", values
        elif acr_headers:
            yield "Access-Control-Allow-Headers", acr_headers

        if self.expose_headers is not None:
            values = ", ".join(self.expose_headers)
            yield "Access-Control-Expose-Headers", values
