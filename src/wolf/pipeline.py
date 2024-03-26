from typing import Callable, Sequence
from functools import update_wrapper


Wrapper = Callable[[Callable], Callable]


def chain_wrap(chain: Sequence[Wrapper], endpoint: Callable) -> Callable:
    wrapped = endpoint
    for middleware in reversed(chain):
        wrapping = middleware(wrapped)
        update_wrapper(wrapping, wrapped)
        wrapped = wrapping
    return wrapped
