import typing as t
from wolf.wsgi.request import WSGIRequest
from wolf.plugins import ServiceManager, Configuration, factory


class Message(t.NamedTuple):
    body: str
    type: str = "info"

    def to_dict(self):
        return self._asdict()


class SessionMessages:

    def __init__(self, session: HTTPSession, key: str = "flashmessages"):
        self.key = key
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


class Flash(ServiceManager, Configuration):
    key: str = "flashmessages"
    __dependencies__ = [HTTPSession]

    @factory("scoped")
    def messages_factory(self, scope: Scope) -> SessionMessages:
        session = scope.get(HTTPSession)
        return SessionMessages(session, key=self.key)
