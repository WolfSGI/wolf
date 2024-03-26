from dataclasses import dataclass
from http_session import Session
from aioinject import Object, Scoped
from wolf.http.request import Request
from wolf.identity import Authenticator, Source, User, anonymous
from wolf.pluggability import Installable


@dataclass(kw_only=True)
class SessionAuthenticator(Installable, Authenticator):

    user_key: str
    sources: tuple[Source, ...]

    def from_credentials(self,
                         request: Request, credentials: dict) -> User | None:
        for source in self.sources:
            user = source.find(credentials, request)
            if user is not None:
                return user

    def install(self, application):
        application.services.register(Object(self, type_=Authenticator))
        application.services.register(Scoped(self.identify))

    def identify(self, request: Request) -> User:
        session = request.get(Session)
        if (userid := session.get(self.user_key, None)) is not None:
            for source in self.sources:
                user = source.fetch(userid, request)
                if user is not None:
                    return user
        return anonymous

    def forget(self, request: Request) -> None:
        session = request.get(Session)
        session.clear()

    def remember(self, request: Request, user: User) -> None:
        session = request.get(Session)
        session[self.user_key] = user.id
