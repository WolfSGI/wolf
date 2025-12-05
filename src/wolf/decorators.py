import inspect
from functools import wraps
from kettu.http.request import Request
from kettu.utils import method_dependencies


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
