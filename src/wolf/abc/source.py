import abc
import typing as t
from wolf.abc.request import RequestProtocol
from wolf.abc.auth import Source, SourceAction
from wolf.abc.identity import User, UserID


class Create(SourceAction):

    @abc.abstractmethod
    def create(self, data: dict):
        pass


class Update(SourceAction):

    @abc.abstractmethod
    def update(self, uid: UserID, data: dict) -> bool:
        pass


class Delete(SourceAction):

    @abc.abstractmethod
    def delete(self, uid: UserID) -> bool:
        pass


class Search(SourceAction):

    @abc.abstractmethod
    def search(
            self, criterions: dict, index: int = 0, size: int = 10
    ) -> t.Iterator[User]:
        pass

    @abc.abstractmethod

    def count(self, criterions: dict) -> int:
        pass


class Challenge(SourceAction):

    @abc.abstractmethod
    def challenge(self, credentials: dict) -> User | None:
        pass
