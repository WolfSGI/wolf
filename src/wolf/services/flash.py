import typing as t
from aioinject import Scoped
from http_session import Session
from wolf.pluggability import Installable, install_method


class Message(t.NamedTuple):
    body: str
    type: str = "info"

    def to_dict(self):
        return self._asdict()


class SessionMessages:
    key: str = "flashmessages"

    def __init__(self, session: Session):
        self.session = session

    def __iter__(self) -> t.Iterable[Message]:
        if self.key in self.session:
            while self.session[self.key]:
                yield Message(**self.session[self.key].pop(0))
                self.session.save()

    def add(self, body: str, type: str = "info"):
        if self.key in self.session:
            messages = self.session[self.key]
        else:
            messages = self.session[self.key] = []
        messages.append({"type": type, "body": body})
        self.session.save()


class Flash(Installable):
    @install_method(object)
    def register_services(self, application):
        application.services.register(Scoped(SessionMessages))
