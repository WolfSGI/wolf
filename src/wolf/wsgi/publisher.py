import re
from abc import ABC, abstractmethod
from collections import deque
from kettu.http.response import Response
from kettu.registries import Registry, Proxy
from kettu.traversing import Traversed
from urllib.parse import unquote
from plum import Signature


class PublicationRoot:
    pass


class PublicationError(Exception):
    pass


def consumer_sorter(result: tuple[Signature, Proxy]):
    return result[1].__metadata__.order


class ConsumerRegistry(Registry):

    def consumers_for(self, obj: object):
        for consumer in self.lookup(obj, None, sorter=consumer_sorter):
            yield consumer(obj)


base_consumers = ConsumerRegistry()


NOT_FOUND = object()


class BaseConsumer(ABC):

    def __init__(self, context):
        self.context = context

    @abstractmethod
    def resolve(self, obj, name: str, request):
        ...

    def __call__(self, request, obj, stack):
        name = stack.popleft()
        found = self.resolve(obj, name, request)
        if found is NOT_FOUND:
            # Nothing was found, we restore the stack.
            stack.appendleft(name)
            return False, obj, stack

        resolved = Traversed(
            found, parent=self.context, path=f"/{name}", name=name)
        return True, resolved, stack


@base_consumers.register((object,), order=999)
class ItemConsumer(BaseConsumer):
    """Default path consumer for model lookup, traversing objects
    using their attributes or, as second choice, contained items.
    """
    def resolve(self, obj, name, request):
        if hasattr(obj, '__getitem__'):
            try:
                return obj[name]
            except (KeyError, TypeError):
                pass
        return NOT_FOUND


class Publisher:
    """A publisher using model and view lookup components.
    """
    def __init__(self, consumers: ConsumerRegistry = base_consumers):
        self.consumers = consumers

    def publish(self, request, obj):
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
