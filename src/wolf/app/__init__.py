from collections import defaultdict
from dataclasses import dataclass, field

import svcs
import structlog
from kettu.exceptions import HTTPError
from wolf.pipeline import Wrapper, chain_wrap
from wolf.abc.resolvers import URIResolver, Params, Extra
from wolf.app.nodes import Mapping, Node
from wolf.app.response import Response
from wolf.app.request import Request
from wolf.wsgi.types import WSGIEnviron, WSGICallable, ExceptionInfo
from wolf.utils import immutable_cached_property
from wolf.app.pluggability import Installable
from wolf.app.events import Events


logger = structlog.get_logger("wolf.app")


@dataclass(kw_only=True, repr=False)
class Application(Node):
    resolver: URIResolver
    events: Events = field(default_factory=Events)
    services: svcs.Registry = field(default_factory=svcs.Registry)
    middlewares: tuple[Wrapper, ...] = field(default_factory=tuple)
    sinks: Mapping = field(default_factory=Mapping)

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
        self.events.lifecycle.on_error.send(self, exc_info=exc_info)
        return Response(500, str(err))

    def use(self, *components: Installable):
        logger.info(f"Installing new components on {self}.")
        for component in components:
            logger.info(f"Installing {component}.")
            component.install(self)

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

        request: Request = Request(environ)
        self.events.lifecycle.on_request.send(self, request=request)
        with request(self.services):
            try:
                response = self.endpoint(request)
                self.events.lifecycle.on_response.send(
                    self, response=response)
                return response
            except HTTPError as err:
                logger.debug(err, exc_info=True)
                raise
            except Exception as err:
                logger.critical(err, exc_info=True)
                raise
