import inspect
from functools import wraps
from kettu.http.request import Request
from kettu.utils import method_dependencies


def ondemand(func):

    sig = inspect.signature(func)

    @wraps(func)
    def dispatch(request: Request, *args, **kwargs):
        nonlocal sig

        if request.context is None:
            raise AssertionError('Request does not provide a context.')

        mapper = {
            dependency.name: request.get(dependency.type_)
            for dependency in method_dependencies(func)
        }
        bound = sig.bind(**mapper)
        return func(*bound.args, **bound.kwargs)
    return dispatch
