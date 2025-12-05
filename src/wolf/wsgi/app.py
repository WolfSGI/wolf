import structlog
import svcs
from dataclasses import dataclass, field
from autorouting import MatchedRoute
from kettu.http.exceptions import HTTPError
from kettu.http.app import Application
from kettu.pipeline import Wrapper, chain_wrap
from kettu.routing.router import Router, Params, Extra
from kettu.traversing.traverser import Traverser, ViewRegistry
from wolf.wsgi.publisher import Publisher, PublicationRoot
from wolf.wsgi.nodes import Mapping, Node
from wolf.wsgi.response import WSGIResponse, FileWrapperResponse
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.types import WSGIEnviron, WSGICallable, ExceptionInfo


logger = structlog.get_logger("wolf.wsgi.app")


@dataclass(kw_only=True, repr=False)
class WSGIApplication(Application, Node):
    services: svcs.Registry = field(default_factory=svcs.Registry)
    middlewares: tuple[Wrapper, ...] = field(default_factory=tuple)
    sinks: Mapping = field(default_factory=Mapping)

    def __post_init__(self):
        self.services.register_value(Application, self)

    def endpoint(
            self,
            request: WSGIRequest
    ) -> WSGIResponse | FileWrapperResponse:
        raise NotImplementedError('Override.')


    def handle_exception(self, exc_info: ExceptionInfo, environ: WSGIEnviron):
        typ, err, tb = exc_info
        logger.critical(err, exc_info=False)
        return WSGIResponse(500, str(err))

    def finalize(self):
        # everything that needs doing before serving requests.
        if self.middlewares:
            self.endpoint = chain_wrap(self.middlewares, self.endpoint)

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
        request.context.register_local_value(Extra, extra)
        route: MatchedRoute | None = self.router.get(
            request.path, request.method, extra=extra
        )
        if route is None:
            raise HTTPError(404)

        # Register the route and its params.
        # No need to guess the type. For optimization purposes,
        # we provide it.
        request.context.register_local_value(MatchedRoute, route)
        request.context.register_local_value(Params, route.params)
        return route.routed(request)


@dataclass(kw_only=True, repr=False)
class TraversingApplication(WSGIApplication):
    factories: Traverser = field(default_factory=Traverser)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def __post_init__(self):
        super().__post_init__()
        self.services.register_factory(Params, Params)
        self.services.register_factory(Extra, Extra)

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
        request.context.register_local_value(MatchedRoute, view)
        return view.routed(request, context=leaf)


@dataclass(kw_only=True, repr=False)
class PublishingApplication(WSGIApplication):
    publisher: Publisher = field(default_factory=Publisher)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def __post_init__(self):
        super().__post_init__()
        self.services.register_factory(Params, Params)
        self.services.register_factory(Extra, Extra)

    def finalize(self):
        # everything that needs doing before serving requests.
        self.views.finalize()
        super().finalize()

    def endpoint(
            self,
            request: WSGIRequest
    ) -> WSGIResponse | FileWrapperResponse:

        root = request.get(PublicationRoot)
        leaf, view_path = self.publisher.publish(request, root)

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
        request.context.register_local_value(MatchedRoute, view)
        return view.routed(request, context=leaf)
