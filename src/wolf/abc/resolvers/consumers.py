from abc import ABC, abstractmethod
from signature_registries import Registry, Proxy
from wolf.abc.resolvers import Located
from plum import Signature


NOT_FOUND = object()


def consumer_sorter(result: tuple[Signature, Proxy]):
    return result[1].__metadata__.order


class ConsumerRegistry(Registry):

    def consumers_for(self, obj: object):
        for consumer in self.lookup(obj, None, sorter=consumer_sorter):
            yield consumer(obj)


base_consumers = ConsumerRegistry()


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

        resolved = Located(
            found, parent=self.context, path=f"/{name}", id=name)
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
