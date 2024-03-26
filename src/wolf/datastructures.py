import typing as t
import bisect
from inspect import isclass
from collections.abc import Hashable


C = t.TypeVar("C")
H = t.TypeVar("H", bound=Hashable)
T = t.TypeVar("T", covariant=True)


class PriorityChain(t.Generic[C]):
    __slots__ = ("_chain",)

    _chain: t.List[t.Tuple[int, C]]

    def __init__(self, *components: C):
        self._chain = list(enumerate(components))

    def __iter__(self):
        return iter(self._chain)

    def add(self, component: C, order: int = 0):
        insert = (order, component)
        if not self._chain:
            self._chain = [insert]
        elif insert in self._chain:
            raise KeyError("Component {component!r} already exists at #{order}.")
        else:
            bisect.insort(self._chain, insert)

    def remove(self, component: C, order: int):
        insert = (order, component)
        if insert not in self._chain:
            raise KeyError("Component {component!r} doest not exist at #{order}.")
        self._chain.remove(insert)

    def clear(self):
        self._chain.clear()


class TypedValue(t.Generic[T, H], t.Dict[t.Type[T], H]):
    __slots__ = ()

    @staticmethod
    def lineage(cls: t.Type[T]):
        yield from cls.__mro__

    def lookup(self, co: t.Type[T] | T) -> t.Iterator[H]:
        cls = isclass(co) and co or co.__class__
        for parent in self.lineage(cls):
            if parent in self:
                yield self[parent]


class TypedSet(t.Generic[T, H], t.Dict[t.Type[T], t.Set[H]]):
    __slots__ = ()

    def add(self, cls: t.Type[T], component: H):
        components = self.setdefault(cls, set())
        components.add(component)

    @staticmethod
    def lineage(cls: t.Type[T]):
        yield from cls.__mro__

    def lookup(self, co: t.Type[T] | T) -> t.Iterator[H]:
        cls = isclass(co) and co or co.__class__
        for parent in self.lineage(cls):
            if parent in self:
                yield from self[parent]

    def __or__(self, other: "TypedSet"):
        new = TypedSet()
        for cls, seq in self.items():
            components = new.setdefault(cls, set())
            components |= seq
        for cls, seq in other.items():
            components = new.setdefault(cls, set())
            components |= seq
        return new

    def __ior__(self, other: "TypedSet"):
        for cls, seq in other.items():
            components = self.setdefault(cls, set())
            components |= seq
        return self
