import logging
from functools import wraps
from dataclasses import dataclass, field
from wolf.cors import CORSPolicy
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.response import WSGIResponse


logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class CORS:
    policy: CORSPolicy

    def __call__(self, handler):
        @wraps(handler)
        def preflight(request: Request, *args, **kwargs) -> WSGIRequest:
            if request.method != 'OPTIONS':
                return handler(scope, *args, **kwargs)

            # We intercept the preflight.
            # If a route was possible registered for OPTIONS,
            # this will override it.
            logger.debug('Cors policy crafting preflight response.')
            origin = request.environ.get('ORIGIN')
            acr_method = request.environ.get(
                'ACCESS_CONTROL_REQUEST_METHOD')
            acr_headers = request.environ.get(
                'ACCESS_CONTROL_REQUEST_HEADERS')
            return WSGIResponse(200, headers=Headers(
                self.policy.preflight(
                    origin=origin,
                    acr_method=acr_method,
                    acr_headers=acr_headers
                )
            ))
        return preflight
