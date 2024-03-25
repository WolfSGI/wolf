from http_session.meta import Session
from wolf.http.request import Request
from wolf.identity import Authenticator, Source, User, anonymous


class SessionAuthenticator(Authenticator):

    user_key: str
    sources: tuple[Source, ...]

    def from_credentials(self,
                         request: Request, credentials: dict) -> User | None:
        for source in self.sources:
            user = source.find(credentials, request)
            if user is not None:
                return user

    @factory('singleton')
    def auth_service(self, request: Request) -> Authenticator:
        return self

    @factory('scoped')
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
