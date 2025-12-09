import structlog
from functools import wraps
from dataclasses import dataclass
from kettu.cors import CORSPolicy
from wolf.abc.request import RequestProtocol
from wolf.abc.response import ResponseProtocol


logger = structlog.get_logger("wolf.middlewares.cors")


@dataclass(kw_only=True)
class CORS:
    policy: CORSPolicy

    def __call__(self, handler):
        @wraps(handler)
        def preflight(
                request: RequestProtocol, *args, **kwargs
        ) -> ResponseProtocol:
            if request.method != "OPTIONS":
                return handler(request, *args, **kwargs)

            # We intercept the preflight.
            # If a route was possible registered for OPTIONS,
            # this will override it.
            logger.debug("Cors policy crafting preflight response.")
            origin = request.environ.get("ORIGIN")
            acr_method = request.environ.get("ACCESS_CONTROL_REQUEST_METHOD")
            acr_headers = request.environ.get("ACCESS_CONTROL_REQUEST_HEADERS")
            return request.response_cls(
                200,
                headers=list(
                    self.policy.preflight(
                        origin=origin,
                        acr_method=acr_method,
                        acr_headers=acr_headers
                    )
                ),
            )

        return preflight
