import structlog
import svcs
from dataclasses import dataclass, field
from autorouting import MatchedRoute
from autorouting.url import RouteURL
from kettu.http.app import Application, URIResolver
from kettu.http.exceptions import HTTPError
from kettu.pipeline import Wrapper, chain_wrap
from kettu.routing import Router, Params, Extra
from kettu.traject import ContextRegistry, ViewRegistry
from kettu.traject.resolver import Located
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.response import WSGIResponse, FileWrapperResponse
from wolf.wsgi.types import WSGIEnviron, WSGICallable, ExceptionInfo


logger = structlog.get_logger("wolf.wsgi.resolvers")


class PathFragment(str):

    def __new__(cls, value: str):
        return super().__new__(cls, str(value).strip('/'))

    def __truediv__(self, other: str):
        if not other or other == '/':
            return self
        return PathFragment('/'.join((self, other.lstrip('/'))))


@dataclass(kw_only=True, repr=False)
class TrajectResolver(URIResolver):

    contexts: ContextRegistry = field(default_factory=ContextRegistry)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def finalize(self):
        self.contexts.finalize()
        self.views.finalize()

    def resolve(self, request):
        app = request.get(Application)
        leaf, view_path = self.contexts.resolve(
            app, request.path, 'GET', request, partial=True
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

    def path_for(self, source: object, name: str, target: object | None = None, **namespace):
        if type(source) is Located:
            root_path = PathFragment(source.__path__)
        else:
            root_path = PathFragment('/')

        if target is not None and source.__class__ is not target.__class__:
            traversal_path = self.contexts.reverse(
                target.__class__,
                source.__class__
            )
            factory_path, unmatched = RouteURL.from_path(
                traversal_path
            ).resolve(namespace, qstring=False)
        else:
            factory_path = ''
            unmatched = {}
            target = source

        view_path = self.views.route_for(target, name, **unmatched)
        return '/' + (root_path / factory_path / view_path)

    def __or__(self, other: "TrajectResolver"):
        return TrajectResolver(
            contexts=(self.contexts | other.contexts),
            views=(self.views | other.views)
        )

    def __ior__(self, other: "TrajectResolver"):
        self.contexts |= other.contexts
        self.views |= other.views
        return self
