import abc
import uuid
import typing as t
from wolf.abc.identity import User, UserID
from wolf.abc.request import RequestProtocol
from wolf.json import JSONSchema


class SourceAction:
    schema: JSONSchema | None
    source: 'Source'
    request: RequestProtocol

    def __init__(self, source: "Source", request: RequestProtocol):
        self.source = source
        self.request = request


class Source(abc.ABC):
    title: str
    description: str
    actions: dict[type[SourceAction], SourceAction]

    def get_action(self, type_: type[SourceAction], request: RequestProtocol):
        if (action := self.actions.get(type_)) is not None:
            return action(self, request)

    @abc.abstractmethod
    def get(self, uid: UserID) -> User | None:
        pass


Preflight = t.Callable[[RequestProtocol], User | None]


class Authenticator(abc.ABC):

    sources: dict[str, Source]
    preflights: list[Preflight]

    @abc.abstractmethod
    def challenge(
            self, request: RequestProtocol, credentials: t.Any
    ) -> User | None:
        pass

    @abc.abstractmethod
    def identify(
            self, request: RequestProtocol
    ) -> User: ...

    @abc.abstractmethod
    def forget(
            self, request: RequestProtocol
    ) -> None: ...

    @abc.abstractmethod
    def remember(
            self, request: RequestProtocol, source_id: str, user: User
    ) -> None: ...
