import logging
from dataclasses import dataclass, field
from aioinject import Container, Object, Scoped
from autorouting import MatchedRoute
from wolf.http.exceptions import HTTPError
from wolf.http.app import Application
from wolf.wsgi.nodes import Mapping, Node
from wolf.wsgi.response import WSGIResponse, FileWrapperResponse
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.types import WSGIEnviron, ExceptionInfo, WSGICallable
from wolf.pipeline import Wrapper, chain_wrap
from wolf.routing.router import Router, Params, Extra
from wolf.traversing.traverser import Traverser, ViewRegistry


logger = logging.getLogger(__name__)


@dataclass(kw_only=True, repr=False)
class WSGIApplication(Application, Node):
    services: Container = field(default_factory=Container)
    middlewares: tuple[Wrapper, ...] = field(default_factory=tuple)
    sinks: Mapping = field(default_factory=Mapping)

    def __post_init__(self):
        self.services.register(Object(self, type_=Application))

    def endpoint(
            self,
            request: WSGIRequest
    ) -> WSGIResponse | FileWrapperResponse:
        raise NotImplementedError('Override.')

    def finalize(self):
        # everything that needs doing before serving requests.
        if self.middlewares:
            self.endpoint = chain_wrap(self.middlewares, self.endpoint)

    def handle_exception(self, exc_info: ExceptionInfo, environ: WSGIEnviron):
        typ, err, tb = exc_info
        logging.critical(err, exc_info=True)
        return WSGIResponse(500, str(err))

    def resolve(self, environ: WSGIEnviron) -> WSGICallable:
        if self.sinks:
            try:
                return self.sinks.resolve(environ)
            except HTTPError as err:
                if err.status != 404:
                    raise err

        wsgi_request = WSGIRequest(environ)
        with wsgi_request(self.services) as request:
            return self.endpoint(request)


@dataclass(kw_only=True, repr=False)
class RoutingApplication(WSGIApplication):
    router: Router = field(default_factory=Router)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.router.finalize()
        super().finalize()

    def endpoint(
            self,
            request: WSGIRequest
    ) -> WSGIResponse | FileWrapperResponse:
        extra = Extra(request=request)
        request.context.register(Object(extra))
        route: MatchedRoute | None = self.router.get(
            request.path, request.method, extra=extra
        )
        if route is None:
            raise HTTPError(404)

        # Register the route and its params.
        # No need to guess the type. For optimization purposes,
        # we provide it.
        request.context.register(Object(route, type_=MatchedRoute))
        request.context.register(Object(route.params, type_=Params))
        return route.routed(request)


@dataclass(kw_only=True, repr=False)
class TraversingApplication(WSGIApplication):
    factories: Traverser = field(default_factory=Traverser)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def __post_init__(self):
        super().__post_init__()
        self.services.register(Scoped(Params))
        self.services.register(Scoped(Extra))

    def finalize(self):
        # everything that needs doing before serving requests.
        self.factories.finalize()
        self.views.finalize()
        super().finalize()

    def endpoint(
            self,
            request: WSGIRequest
    ) -> WSGIResponse | FileWrapperResponse:
        leaf, view_path = self.factories.traverse(
            self, request.path, 'GET', request, partial=True
        )

        if not view_path.startswith('/'):
            view_path = f'/{view_path}'

        extra = request.get(Extra)
        view = self.views.match(
            leaf, view_path, request.method, extra=extra
        )
        if view is None:
            raise HTTPError(404)

        params = request.get(Params)
        params |= view.params

        request.context.register(Object(view, type_=MatchedRoute))
        return view.routed(request, context=leaf)
