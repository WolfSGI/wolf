from inspect import isclass
from wrapt import ObjectProxy
from types import EllipsisType
from collections import UserDict
from typing import (
    Tuple, NamedTuple, Sequence, Literal, Type, Mapping, ClassVar
)

from plum import Signature
from prejudice.errors import ConstraintsErrors
from prejudice.types import Predicate
from prejudice.utils import resolve_constraints
from wolf.registries.resolver import SignatureResolver


DEFAULT = ""
Default = Literal[DEFAULT]


class ProxyMetadata(NamedTuple):
    callable: bool
    isclass: bool
    name: str = ''
    title: str = ''
    description: str = ''
    classifiers: set[str] = set()
    conditions: Sequence[Predicate] | None = None


class Proxy(ObjectProxy):

    __metadata__: ProxyMetadata

    def __init__(self, wrapped, **kwargs):
        super().__init__(wrapped)
        self.__metadata__ = ProxyMetadata(
            callable(wrapped), isclass(wrapped), **kwargs
        )

    def __evaluate__(self, *args, **kwargs) -> ConstraintsErrors | None:
        if self.__metadata__.conditions:
            return resolve_constraints(self.__metadata__.conditions, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.__wrapped__(*args, **kwargs)


def base_sorter(result: Tuple[Signature, Proxy]):
    return result[0], result[1].__metadata__.name


class Registry(UserDict[Signature, ObjectProxy]):

    resolver: SignatureResolver

    def __init__(self, data=None):
        self.resolver = SignatureResolver()
        super().__init__(data)

    def __setitem__(self, signature: Signature, proxy: ObjectProxy):
        self.resolver.register(signature)
        super().__setitem__(signature, proxy)

    def lookup(self, *args, sorter = base_sorter):
        found = []
        for signature, proxy in self.items():
            if signature.match(args):
                found.append((signature, proxy))
        return (r[1] for r in sorted(found, key=sorter))

    def match(self, *args, name: str, sorter = base_sorter):
        return self.lookup(*args, name, sorter=sorter)

    def match_grouped(self, *args, sorter = base_sorter):
        proxies = {}
        for e in self.lookup(*args, None, sorter=sorter):
            name = e.__metadata__.name
            if name not in proxies:
                proxies[name] = e
        return proxies

    def fetch(self, *args, name: str = DEFAULT) -> Proxy:
        match = self.resolver.resolve((*args, name))
        return self[match]

    def register(self,
                 discriminant: Sequence[Type],
                 name: str = DEFAULT, **kwargs):
        def register_resolver(func):
            proxy = Proxy(func, name=name, **kwargs)
            signature = Signature(
                *discriminant, Literal[name] | None)
            self[signature] = proxy
            return func
        return register_resolver


class TypedRegistry(Registry):

    Types: ClassVar[Type[NamedTuple]]

    def register(self,
                 types: Sequence[Type] | Mapping[str, Type] | EllipsisType,
                 name: str = DEFAULT, **kwargs):
        if types is ...:
            discriminant = self.Types()
        elif isinstance(types, Mapping):
            discriminant = self.Types(**types)
        elif isinstance(types, Sequence):
             discriminant = self.Types(*types)
        return super().register(discriminant, name, **kwargs)
