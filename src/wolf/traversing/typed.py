import typing as t
from collections import defaultdict
from autorouting import MatchedRoute
from wolf.pipeline import aggregate
from wolf.routing.router import Router, HTTPMethods, get_routables
from wolf.datastructures import TypedValue


class TypedRouters(TypedValue[t.Any, Router], defaultdict):

    def __init__(self):
        defaultdict.__init__(self, Router)

    def finalize(self):
        for router in self.values():
            router.finalize()

    def add(self, root: t.Type[t.Any], path: str, method: str, factory: t.Callable, **kwargs):
        return self[root].add(path, method, factory, **kwargs)

    def register(self,
                 root: t.Type,
                 path: str,
                 pipeline = None,
                 methods: HTTPMethods | None = None,
                 **kwargs):
        def routing(value: t.Any):
            for endpoint, verbs in get_routables(value, methods):
                if pipeline:
                    endpoint = aggregate(pipeline, endpoint)
                for verb in verbs:
                    self.add(root, path, verb, endpoint, **kwargs)
            return value
        return routing

    def match(self, context: t.Any, path: str, method: str, extra: dict | None = None):
        for router in self.lookup(context.__class__):
            matched: MatchedRoute | None = router.get(path, method, extra=extra)
            if matched is not None:
                return matched

    def route_for(self, context: t.Any, name: str, **params):
        for router in self.lookup(context.__class__):
            route_url = router.get_by_name(name)
            if route_url is not None:
                path, _ = route_url.resolve(params)
                return path

    def __or__(self, other: 'TypedRouters'):
        new = TypedRouters()
        for cls, router in self.items():
            new[cls] = router
        for cls, router in other.items():
            if cls in new:
                new[cls] |= router
            else:
                new[cls] = router
        return new

    def __ior__(self, other: 'TypedRouters'):
        for cls, router in other.items():
            if cls in self:
                self[cls] |= router
            else:
                self[cls] = router
        return self
