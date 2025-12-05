import structlog
import svcs
from dataclasses import dataclass, field
from autorouting import MatchedRoute
from kettu.http.exceptions import HTTPError
from kettu.http.app import URIResolver
from kettu.pipeline import Wrapper, chain_wrap
from kettu.routing import Router, Params, Extra
from kettu.traject import ViewRegistry
from kettu.traversing import Publisher, PublicationRoot
from wolf.wsgi.nodes import Mapping, Node
from wolf.wsgi.response import WSGIResponse, FileWrapperResponse
from wolf.wsgi.request import WSGIRequest
from wolf.wsgi.types import WSGIEnviron, WSGICallable, ExceptionInfo


@dataclass(kw_only=True, repr=False)
class TraversingResolver(URIResolver):

    publisher: Publisher = field(default_factory=Publisher)
    views: ViewRegistry = field(default_factory=ViewRegistry)

    def finalize(self):
        self.views.finalize()

    def resolve(self, request):
        root = request.get(PublicationRoot)
        leaf, view_path = self.publisher.publish(request, root)

        if not view_path.startswith('/'):
            view_path = f'/{view_path}'

        extra = request.get(Extra)
        extra['request'] = request
        view = self.views.match(
            leaf, view_path, request.method, extra=extra
        )
        if view is None:
            raise HTTPError(404)

        params = request.get(Params)
        params.update(view.params)
        request.context.register_local_value(MatchedRoute, view)
        return view.routed(request, context=leaf)

    def path_for(self, *args, **kwargs):
        raise NotImplementedError("Unavailable for Traversing")

    def __or__(self, other: "TraversingResolver"):
        return TrajectResolver(
            publisher=(self.publisher | other.publisher),
            views=(self.views | other.views)
        )

    def __ior__(self, other: "TraversingResolver"):
        self.publisher |= other.publisher
        self.views |= other.views
        return self
