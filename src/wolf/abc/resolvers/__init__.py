from typing import Protocol, Any
from abc import abstractmethod
from wrapt import ObjectProxy
from wolf.abc.request import RequestProtocol
from wolf.abc.response import ResponseProtocol, FileResponseProtocol


class APIView:
    """Marker class that has methods named after HTTP METHODS.
    """
    pass


class Located(ObjectProxy):
    __parent__: Any
    __path__: str
    __id__: str | None

    def __init__(self, wrapped, *,
                 parent: Any, path: str, id: str | None = None):
        super().__init__(wrapped)
        self.__parent__ = parent
        self.__id__ = id
        if type(parent) is Located:
            self.__path__ = f"{parent.__path__}/{path}"
        else:
            self.__path__ = path


class Extra(dict):
    pass


class Params(dict):
    pass


class URIResolver(Protocol):

    def finalize(self) -> None:
        pass

    @abstractmethod
    def resolve(
            self, request: RequestProtocol
    ) -> ResponseProtocol | FileResponseProtocol:
        raise NotImplementedError("this method needs to be overridden.")
