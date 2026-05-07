import typing as t
from wrapt import ObjectProxy
from collections import UserDict


class Contained(ObjectProxy):
    __uri__: str

    def __init__(self, wrapped: t.Any, name: str):
        super().__init__(wrapped)
        self.__uri__ = name


class Container(UserDict):

    def __setitem__(self, key, value):
        value = Contained(value, key)
        super().__setitem__(key, value)
