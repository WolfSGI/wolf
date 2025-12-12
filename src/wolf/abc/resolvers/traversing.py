import re
import typing as t
from collections import deque
from urllib.parse import unquote
from wolf.abc.request import RequestProtocol
from .consumers import ConsumerRegistry, base_consumers
from .consumers import BaseConsumer


class PublicationRoot:
    pass


class Publisher:
    """A publisher using model and view lookup components.
    """
    def __init__(self, consumers: ConsumerRegistry = base_consumers):
        self.consumers = consumers

    def publish(
            self, request: RequestProtocol, obj: PublicationRoot
    ) -> tuple[t.Any, str]:
        path = unquote(request.path)
        stack = deque(re.split(r'/+', path.strip('/')))
        unconsumed = stack.copy()
        while unconsumed:
            for consumer in self.consumers.consumers_for(obj):
                any_consumed, obj, unconsumed = consumer(
                    request, obj, unconsumed)
                if any_consumed:
                    break
            else:
                # nothing could be consumed
                return obj, '/'.join(unconsumed)
        return obj, '/'.join(unconsumed)


__all__ = [
    "PublicationRoot",
    "Publisher",
    "ConsumerRegistry",
    "BaseConsumer",
    "base_consumers",
]
