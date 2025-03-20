from pathlib import PurePosixPath
from functools import wraps
from dataclasses import dataclass, field
from kettu.http.exceptions import HTTPError
from kettu.http.request import Request
from kettu.http.response import Response
from kettu.identity import anonymous, User


@dataclass(kw_only=True)
class NoAnonymous:
    allowed_urls: set[str] = field(default_factory=set)
    login_url: str | None = None

    def __post_init__(self):
        allowed = set((PurePosixPath(url) for url in self.allowed_urls))
        if self.login_url is not None:
            allowed.add(PurePosixPath(self.login_url))
        self.unprotected = frozenset(allowed)

    def __call__(self, handler):
        @wraps(handler)
        def checker(request: Request, *args, **kwargs) -> Response:
            # we skip unnecessary checks if it's not protected.
            path = PurePosixPath(request.path)
            for bypass in self.unprotected:
                if path.is_relative_to(bypass):
                    return handler(request, *args, **kwargs)

            user = request.get(User, default=anonymous)
            if user is anonymous:
                if self.login_url is None:
                    raise HTTPError(401)
                return request.response_cls.redirect(
                    request.root_path + self.login_url
                )
            return handler(request, *args, **kwargs)

        return checker


@dataclass(kw_only=True)
class Protected:
    protected_urls: set[str] = field(default_factory=set)
    login_url: str | None = None

    def __post_init__(self):
        protected = set((PurePosixPath(url) for url in self.protected_urls))
        self.protected = frozenset(protected)

    def __call__(self, handler):
        @wraps(handler)
        def checker(request: Request, *args, **kwargs) -> Response:
            # we skip unnecessary checks if it's not protected.
            path = PurePosixPath(request.path)
            for protected in self.protected:
                if path.is_relative_to(protected):
                    user = request.get(User, default=anonymous)
                    if user is anonymous:
                        if self.login_url is None:
                            raise HTTPError(401)
                        return request.response_cls.redirect(
                            request.root_path + self.login_url
                        )

            return handler(request, *args, **kwargs)
        return checker
