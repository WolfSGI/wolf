from functools import wraps, cache
from inspect import Signature
from types import FunctionType
from typing import NamedTuple
from wolf.abc.request import RequestProtocol


class Dependency(NamedTuple):
    name: str
    type_: type


@cache
def method_dependencies(
        method: FunctionType | type) -> list[Dependency]:
    sig = Signature.from_callable(method)
    return [Dependency(name=key, type_=value.annotation)
            for key, value in sig.parameters.items()]


def ondemand(func):

    dependencies = method_dependencies(func)

    @wraps(func)
    def dispatch(request: RequestProtocol, *args, **kwargs):
        nonlocal dependencies

        mapper = {}
        for dependency in dependencies:
            if dependency.name in kwargs:
                mapper[dependency.name] = kwargs[dependency.name]
            else:
                mapper[dependency.name] = request.get(dependency.type_)
        return func(**mapper)
    return dispatch
