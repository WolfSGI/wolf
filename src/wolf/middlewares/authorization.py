from pathlib import PurePosixPath
from functools import wraps
from dataclasses import dataclass, field
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.response import WSGIResponse
from wolf.identity import anonymous, User


class NoAnonymous:
    allowed_urls: t.Set[str] = field(default_factory=set)
    login_url: str | None = None

    def __post_init__(self):
        allowed = set((PurePosixPath(url) for url in self.allowed_urls))
        if self.login_url is not None:
            allowed.add(PurePosixPath(self.login_url))
        self.unprotected = frozenset(allowed)

    def __call__(self, handler):
        @wraps(handler)
        def checker(request: WSGIRequest, *args, **kwargs) -> WSGIResponse:

            # we skip unnecessary checks if it's not protected.
            path = PurePosixPath(request.path)
            for bypass in self.unprotected:
                if path.is_relative_to(bypass):
                    return handler(request, *args, **kwargs)

            user = request.context.get(User)
            if user is anonymous:
                if self.login_url is None:
                    raise HTTPError(403)
                return WSGIResponse.redirect(
                    request.root_path + self.login_url
                )
            return handler(request, *args, **kwargs)
        return checker
