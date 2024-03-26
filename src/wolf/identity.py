import abc
import uuid
import typing as t
from wolf.http.request import Request


UserID = str | int | uuid.UUID


class User(abc.ABC):
    id: UserID


class AnonymousUser(User):
    id: int = -1


anonymous = AnonymousUser()


class Source(abc.ABC):
    @abc.abstractmethod
    def find(self, credentials: t.Any, request: Request) -> User | None:
        pass

    @abc.abstractmethod
    def fetch(self, uid: UserID, request: Request) -> User | None:
        pass


class DictSource(Source):
    def __init__(self, users: dict[str, str]):
        self.users = users

    def find(self, credentials: dict, request: Request) -> User | None:
        username = credentials.get("username")
        password = credentials.get("password")
        if username is not None and username in self.users:
            if self.users[username] == password:
                user = User()
                user.id = username
                return user

    def fetch(self, uid: UserID, request: Request) -> User | None:
        if uid in self.users:
            user = User()
            user.id = uid
            return user


class Authenticator(abc.ABC):
    @abc.abstractmethod
    def from_credentials(self, request: Request, credentials: dict) -> User | None: ...

    @abc.abstractmethod
    def identify(self, request: Request) -> User: ...

    @abc.abstractmethod
    def forget(self, request: Request) -> None: ...

    @abc.abstractmethod
    def remember(self, request: Request, user: User) -> None: ...
