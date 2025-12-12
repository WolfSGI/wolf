from dataclasses import dataclass, field
from kettu.exceptions import HTTPError
from wolf.abc.resolvers import URIResolver, Params, Extra
from wolf.abc.resolvers.routing import MatchedRoute
from wolf.abc.resolvers.traject import ViewRegistry
from wolf.abc.resolvers.traversing import Publisher, PublicationRoot


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
        return TraversingResolver(
            publisher=(self.publisher | other.publisher),
            views=(self.views | other.views)
        )

    def __ior__(self, other: "TraversingResolver"):
        self.publisher |= other.publisher
        self.views |= other.views
        return self
