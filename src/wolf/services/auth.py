from winkel.meta import HTTPSession
from winkel.scope import Scope
from winkel.plugins import ServiceManager, Configuration, factory
from winkel.auth import Authenticator, Source, User, anonymous


class SessionAuthenticator(Authenticator, ServiceManager, Configuration):
    __dependencies__ = [HTTPSession]
    __provides__ = [Authenticator, User]

    user_key: str
    sources: tuple[Source, ...]

    def from_credentials(self,
                         scope: Scope, credentials: dict) -> User | None:
        for source in self.sources:
            user = source.find(credentials, scope)
            if user is not None:
                return user

    @factory('singleton')
    def auth_service(self, scope: Scope) -> Authenticator:
        return self

    @factory('scoped')
    def identify(self, scope: Scope) -> User:
        session = scope.get(HTTPSession)
        if (userid := session.get(self.user_key, None)) is not None:
            for source in self.sources:
                user = source.fetch(userid, scope)
                if user is not None:
                    return user
        return anonymous

    def forget(self, scope: Scope) -> None:
        session = scope.get(HTTPSession)
        session.clear()

    def remember(self, scope: Scope, user: User) -> None:
        session = scope.get(HTTPSession)
        session[self.user_key] = user.id
