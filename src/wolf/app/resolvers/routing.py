import structlog
from dataclasses import dataclass, field
from kettu.exceptions import HTTPError
from wolf.abc.resolvers import URIResolver, Params, Extra
from wolf.abc.resolvers.routing import Router, MatchedRoute


logger = structlog.get_logger("wolf.app.resolvers")


@dataclass(kw_only=True, repr=False)
class RouteResolver(URIResolver):

    router: Router = field(default_factory=Router)

    def finalize(self):
        self.router.finalize()

    def resolve(self, request):
        extra = request.get(Extra)
        extra['request'] = request

        route: MatchedRoute | None = self.router.get(
            request.path, request.method, extra=extra
        )
        if route is None:
            raise HTTPError(404)

        params = request.get(Params)
        params.update(route.params)
        # Register the route and its params.
        # No need to guess the type. For optimization purposes,
        # we provide it.
        request.context.register_local_value(MatchedRoute, route)
        return route.routed(request)

    def path_for(self, name: str, **namespace):
        return self.router.path_for(name, **namespace)

    def __or__(self, other: "RouteResolver"):
        return RouteResolver(router=(self.router | other.router))

    def __ior__(self, other: "RouteResolver"):
        self.router |= other.router
        return self
