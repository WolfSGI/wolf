from functools import wraps, cache
from inspect import Signature
from types import FunctionType
from typing import NamedTuple
from kettu.http.request import Request


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
    def dispatch(request: Request, *args, **kwargs):
        nonlocal dependencies

        if request.context is None:
            raise AssertionError('Request does not provide a context.')

        mapper = {
            dependency.name: request.get(dependency.type_)
            for dependency in dependencies
        }
        return func(**mapper)
    return dispatch
