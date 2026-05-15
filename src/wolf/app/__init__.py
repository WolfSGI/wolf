import structlog
import svcs
from collections import defaultdict
from dataclasses import dataclass, field
from kettu.exceptions import HTTPError
from wolf.pipeline import Wrapper, chain_wrap
from wolf.abc.resolvers import URIResolver, Params, Extra
from wolf.app.nodes import Mapping, Node
from wolf.app.response import Response
from wolf.app.request import Request
from wolf.wsgi.types import WSGIEnviron, WSGICallable, ExceptionInfo
from wolf.utils import immutable_cached_property
from wolf.app.pluggability import Installable


logger = structlog.get_logger("wolf.app")


@dataclass(kw_only=True, repr=False)
class Application(Node):
    resolver: URIResolver
    services: svcs.Registry = field(default_factory=svcs.Registry)
    middlewares: tuple[Wrapper, ...] = field(default_factory=tuple)
    sinks: Mapping = field(default_factory=Mapping)
    hooks: dict[str, list] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self):
        self.services.register_value(Application, self)
        self.services.register_value(URIResolver, self.resolver)
        self.services.register_factory(Params, Params)
        self.services.register_factory(Extra, Extra)

    def handle_exception(self, exc_info: ExceptionInfo, environ: WSGIEnviron):
        """Override from the Node class to handle errors are 500 responses.
        """
        typ, err, tb = exc_info
        logger.critical(err, exc_info=False)
        return Response(500, str(err))

    def use(self, *components: Installable):
        logger.info(f"Installing new components on {self}.")
        for component in components:
            logger.info(f"Installing {component}.")
            component.install(self)

    def listen(self, name: str, func):
        logger.debug(f"Added hook handler for {name}: {func}.")
        self.hooks[name].append(func)

    def hook(self, __hook__: str, **kwargs):
        logger.debug(f"Triggering hook: {name} with {kwargs} as args.")
        for func in self.hooks[__hook__]:
            result = func(**kwargs)

    @immutable_cached_property
    def endpoint(self):
        return chain_wrap(
            self.middlewares,
            self.resolver.resolve
        )

    def resolve(self, environ: WSGIEnviron) -> WSGICallable:
        logger.debug(f"{self} got a request.")
        if self.sinks:
            try:
                return self.sinks.resolve(environ)
            except HTTPError as err:
                if err.status != 404:
                    raise err

        request: Request = Request(environ)
        with request(self.services):
            try:
                response = self.endpoint(request)
                logger.debug(f"{self} responds with a {response.status}.")
                return response
            except HTTPError as err:
                logger.debug(err, exc_info=True)
                raise
            except Exception as err:
                logger.critical(err, exc_info=True)
                raise
