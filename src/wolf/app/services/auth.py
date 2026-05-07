import typing as t
import structlog

from dataclasses import dataclass
from http_session import Session

from authsources.authenticator import Authenticator
from authsources.protocols import Challenge, Preflight, Getter
from authsources.source import Source
from authsources.identity import User
from wolf.container import Container
from wolf.app.pluggability import Installable
from wolf.app.request import Request


logger = structlog.get_logger("wolf.app.services.auth")


class AuthenticationInfo(t.TypedDict):
    source_id: str
    user_id: str


class BaseAuthenticator(Installable, Authenticator):

    sources: dict[str, Source]

    def __init__(self, sources: t.Mapping[str, Source] | None = None):
        self.sources = Container(sources is not None and sources or {})

    def install(self, application):
        application.services.register_value(Authenticator, self)
        application.services.register_factory(
            User,
            lambda svcs_container: self.identify(
                svcs_container.get(Request)
            )
        )

    def challenge(
            self, request: Request, credentials: dict
    ) -> tuple[str, User] | tuple[None, None]:
        for source in self.sources.values():
            if Challenge in source:
                bound = source.bind(request=request)
                action = bound.get(Challenge)
                user = action.challenge(credentials)
                if user is not None:
                    return source.__uri__, user
        return None, None

    def identify(self, request) -> User | None:
        for source in self.sources.values():
            if action := source.get(Preflight):
                logger.info(f'Preflight found: {source.title}')
                user = action.preflight(request)
                if user is not None:
                    logger.info(
                        f'Preflight user found by {source.title}: {user}.')
                    return user
                logger.info('Authentication preflight unsuccessful.')

        logger.info('Authentication initiated.')
        if (info := self.get_stored_info(request)) is not None:
            source = self.sources[info['source_id']]
            if Getter in source:
                bound = source.bind(request=request)
                action = bound.get(Getter)
                user = action.get(info['user_id'])
                if user is not None:
                    logger.info(
                        f"Source {info['source_id']} found: {user}")
                    return user
            else:
                logger.warning(
                    f"Source {info['source_id']}: No getter action.")

        return None

    def get_stored_info(self, request) -> AuthenticationInfo:
        pass

    def forget(self, request) -> None:
        pass

    def remember(self, request, source_id: str, user: User) -> None:
        pass


@dataclass(kw_only=True)
class SessionAuthenticator(BaseAuthenticator):
    user_key: str

    def __init__(self, *,
                 user_key, sources: t.Mapping[str, Source] | None = None):
        self.user_key = user_key
        super().__init__(sources=sources)

    def get_stored_info(self, request: Request) -> AuthenticationInfo:
        session = request.get(Session)
        return session.get(self.user_key, None)

    def forget(self, request: Request) -> None:
        session = request.get(Session)
        session.clear()

    def remember(
            self, request: Request, source_id: str, user: User) -> None:
        session = request.get(Session)
        session[self.user_key] = AuthenticationInfo(
            user_id=user.id,
            source_id=source_id
        )
        request.context.register_local_value(User, user)
        if source_id:
            request.context.register_local_value(
                Source, self.sources[source_id])
