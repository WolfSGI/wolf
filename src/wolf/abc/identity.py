import abc
import uuid
import typing as t


UserID = str | int | uuid.UUID


class User(abc.ABC):
    id: UserID


class AnonymousUser(User):
    id: int = -1


anonymous = AnonymousUser()
