from dataclasses import dataclass
from collections.abc import Iterator, Sequence
from wolf.http.types import HTTPMethod


Header = tuple[str, str]


@dataclass
class CORSPolicy:
    origin: str = "*"
    methods: Sequence[HTTPMethod] | None = None
    allow_headers: Sequence[str] | None = None
    expose_headers: Sequence[str] | None = None
    credentials: bool | None = None
    max_age: int | None = None

    def headers(self) -> Iterator[Header]:
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
        origin: str | None = None,
        acr_method: str | None = None,
        acr_headers: str | None = None,
    ) -> Iterator[Header]:
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
