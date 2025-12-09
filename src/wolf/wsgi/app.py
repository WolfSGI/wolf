import structlog
import svcs
from dataclasses import dataclass, field
from kettu.exceptions import HTTPError
from wolf.pipeline import Wrapper, chain_wrap
from wolf.abc.resolvers import URIResolver, Params, Extra
from wolf.wsgi.nodes import Mapping, Node
from wolf.wsgi.response import Response
from wolf.wsgi.request import Request
from wolf.wsgi.types import WSGIEnviron, WSGICallable, ExceptionInfo
from wolf.utils import immutable_cached_property
from wolf.pluggability import Installable


logger = structlog.get_logger("wolf.wsgi.app")


@dataclass(kw_only=True, repr=False)
class Application(Node):
    resolver: URIResolver
    services: svcs.Registry = field(default_factory=svcs.Registry)
    middlewares: tuple[Wrapper, ...] = field(default_factory=tuple)
    sinks: Mapping = field(default_factory=Mapping)

    def __post_init__(self):
        self.services.register_value(Application, self)
        self.services.register_value(URIResolver, self.resolver)
        self.services.register_factory(Params, Params)
        self.services.register_factory(Extra, Extra)

    def handle_exception(self, exc_info: ExceptionInfo, environ: WSGIEnviron):
        typ, err, tb = exc_info
        logger.critical(err, exc_info=False)
        return Response(500, str(err))

    def use(self, *components: Installable):
        for component in components:
            component.install(self)

    def finalize(self):
        self.resolver.finalize()

    @immutable_cached_property
    def endpoint(self):
        return chain_wrap(
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

        request = Request(environ)
        with request(self.services) as scoped_request:
            try:
                return self.endpoint(scoped_request)
            except HTTPError as err:
                logger.debug(err, exc_info=True)
                raise
            except Exception as err:
                logger.critical(err, exc_info=True)
                raise
