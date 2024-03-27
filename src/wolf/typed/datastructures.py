from typing import TypeVar, Generic
from inspect import isclass
from collections.abc import Hashable, Iterator


H = TypeVar("H", bound=Hashable)
T = TypeVar("T", covariant=True)


class TypedValue(Generic[T, H], dict[type[T], H]):
    __slots__ = ()

    @staticmethod
    def lineage(cls: type[T]):
        yield from cls.__mro__

    def lookup(self, co: type[T] | T) -> Iterator[H]:
        cls = isclass(co) and co or co.__class__
        for parent in self.lineage(cls):
            if parent in self:
                yield self[parent]


class TypedSet(Generic[T, H], dict[type[T], set[H]]):
    __slots__ = ()

    def add(self, cls: type[T], component: H):
        components = self.setdefault(cls, set())
        components.add(component)

    @staticmethod
    def lineage(cls: type[T]):
        yield from cls.__mro__

    def lookup(self, co: type[T] | T) -> Iterator[H]:
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
