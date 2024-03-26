from functools import wraps
from wolf.http.request import Request
from wolf.utils import method_dependencies


def ondemand(func):
    @wraps(func)
    def dispatch(request: Request, *args, **kwargs):
        if request.context is None:
            raise AssertionError('Request does not provide a context.')
        dependencies = method_dependencies(func)
        return request.context.execute(func, dependencies, **kwargs)
    return dispatch
