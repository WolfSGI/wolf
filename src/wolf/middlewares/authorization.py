from pathlib import PurePosixPath
from functools import wraps
from dataclasses import dataclass, field
from wolf.http.exceptions import HTTPError
from wolf.http.request import Request
from wolf.http.response import Response
from wolf.identity import anonymous, User


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

            user = request.context.resolve(User)
            if user is anonymous:
                if self.login_url is None:
                    raise HTTPError(403)
                return request.response_cls.redirect(
                    request.root_path + self.login_url
                )
            return handler(request, *args, **kwargs)
        return checker
