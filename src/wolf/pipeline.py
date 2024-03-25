from typing import Callable, Sequence
from functools import update_wrapper
from wolf.datastructures import PriorityChain
from wolf.http.response import Response


Handler = Callable[[...], Response]
HandlerWrapper = Callable[[Handler], Handler]


def aggregate(
        chain: Sequence[HandlerWrapper],
        endpoint: Handler
) -> Handler:

    wrapped = endpoint
    for middleware in reversed(chain):
        wrapping = middleware(wrapped)
        update_wrapper(wrapping, wrapped)
        wrapped = wrapping
    return wrapped


class Pipeline(PriorityChain[HandlerWrapper]):

    def wrap(self, wrapped: Handler) -> Handler:
        chain = [m[1] for m in self._chain]
        return aggregate(chain, wrapped)
