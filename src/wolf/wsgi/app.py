import structlog
import svcs
from dataclasses import dataclass, field
from kettu.http.exceptions import HTTPError
from kettu.http.app import Application, URIResolver
from kettu.pipeline import Wrapper, chain_wrap
from kettu.routing import Params, Extra
from wolf.wsgi.nodes import Mapping, Node
from wolf.wsgi.response import WSGIResponse, FileWrapperResponse
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.types import WSGIEnviron, WSGICallable, ExceptionInfo


logger = structlog.get_logger("wolf.wsgi.app")


@dataclass(kw_only=True, repr=False)
class WSGIApplication(Application, Node):
    resolver: URIResolver
    services: svcs.Registry = field(default_factory=svcs.Registry)
    middlewares: tuple[Wrapper, ...] = field(default_factory=tuple)
    sinks: Mapping = field(default_factory=Mapping)
    endpoint = None

    def __post_init__(self):
        self.services.register_value(Application, self)
        self.services.register_factory(Params, Params)
        self.services.register_factory(Extra, Extra)

    def handle_exception(self, exc_info: ExceptionInfo, environ: WSGIEnviron):
        typ, err, tb = exc_info
        logger.critical(err, exc_info=False)
        return WSGIResponse(500, str(err))

    def finalize(self):
        # everything that needs doing before serving requests.
        self.resolver.finalize()
        if self.middlewares:
            self.endpoint = chain_wrap(
                self.middlewares,
                self.resolver.resolve
            )

    def resolve(self, environ: WSGIEnviron) -> WSGICallable:
        if self.sinks:
            try:
                return self.sinks.resolve(environ)
            except HTTPError as err:
                if err.status != 404:
                    raise err

        wsgi_request = WSGIRequest(environ)
        with wsgi_request(self.services) as request:
            try:
                return self.endpoint(request)
            except HTTPError as err:
                logger.debug(err, exc_info=True)
                raise
            except Exception as err:
                logger.critical(err, exc_info=True)
                raise
