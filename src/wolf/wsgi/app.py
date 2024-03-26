import logging
from dataclasses import dataclass, field
from aioinject import Container, Object
from autorouting import MatchedRoute
from wolf.http.exceptions import HTTPError
from wolf.wsgi.nodes import Mapping, Node
from wolf.wsgi.response import WSGIResponse
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.types import WSGIEnviron, ExceptionInfo, WSGICallable
from wolf.pipeline import HandlerWrapper, aggregate
from wolf.pluggability import Installable
from wolf.routing.router import Router, Params


logger = logging.getLogger(__name__)


class Mounts(Mapping):
    def add(self, app: Node, path: str):
        self[path] = app


@dataclass(kw_only=True, repr=False)
class Root(Node):
    services: Container = field(default_factory=Container)
    middlewares: list[HandlerWrapper] = field(default_factory=list)
    mounts: Mounts = field(default_factory=Mounts)

    def __post_init__(self):
        self.services.register(Object(self, type_=Root))

    def finalize(self):
        # everything that needs doing before serving requests.
        if self.middlewares:
            self.endpoint = aggregate(self.middlewares, self.endpoint)

    def use(self, *components: Installable):
        for component in components:
            component.install(self)

    def handle_exception(self, exc_info: ExceptionInfo, environ: WSGIEnviron):
        typ, err, tb = exc_info
        logging.critical(err, exc_info=True)
        return WSGIResponse(500, str(err))

    def endpoint(self, request: WSGIRequest) -> WSGICallable:
        raise NotImplementedError("Implement your own.")

    def resolve(self, environ: WSGIEnviron) -> WSGICallable:
        if self.mounts:
            try:
                mounted = self.mounts.resolve(environ)
            except HTTPError as err:
                if err.status != 404:
                    raise err
            else:
                return mounted.resolve(environ)

        request = WSGIRequest(environ)
        with self.services.sync_context(extensions=(request,)) as context:
            request.set_context(context)
            try:
                response = self.endpoint(request)
            except HTTPError as err:
                response = request.response_cls(err.status, err.body)
            return response


@dataclass(kw_only=True, repr=False)
class RoutingApplication(Root):
    router: Router = field(default_factory=Router)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.router.finalize()
        super().finalize()

    def endpoint(self, request: WSGIRequest) -> WSGICallable:
        route: MatchedRoute | None = self.router.get(request.path, request.method)
        if route is None:
            raise HTTPError(404)

        # Register the route and its params.
        # No need to guess the type. For optimization purposes, we provide it.
        request.context.register(Object(route, type_=MatchedRoute))
        request.context.register(Object(route.params, type_=Params))
        return route.routed(request)
