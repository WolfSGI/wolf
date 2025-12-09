import typing as t
from dataclasses import dataclass
from http_session import Session
from wolf.pluggability import Installable


class Message(t.NamedTuple):
    body: str
    type: str = "info"

    def to_dict(self):
        return self._asdict()


class SessionMessages:

    def __init__(self, session: Session, key: str):
        self.session = session
        self.key = key

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


@dataclass(kw_only=True)
class Flash(Installable):

    key: str = "flashmessages"

    def install(self, application):
        application.services.register_factory(
            SessionMessages,
            lambda svcs_container: self.session_messages(
                svcs_container.get(Session)
            )
        )

    def session_messages(self, session: Session) -> SessionMessages:
        return SessionMessages(session, key=self.key)
