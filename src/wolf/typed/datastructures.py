import typing as t
from inspect import isclass
from collections.abc import Hashable


H = t.TypeVar("H", bound=Hashable)
T = t.TypeVar("T", covariant=True)


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
