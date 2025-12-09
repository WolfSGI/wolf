import abc
import typing as t
import logging
from wrapt import ObjectProxy
from types import MappingProxyType
from dataclasses import dataclass
from http_session import Session
from wolf.abc.identity import User, anonymous
from wolf.abc.auth import SourceAction, Source, Authenticator, Preflight
from wolf.abc.source import Challenge
from wolf.wsgi.request import Request
from wolf.pluggability import Installable


logger = logging.getLogger(__name__)


class AuthenticationInfo(t.TypedDict):
    source_id: str
    user_id: str



class SourceProxy(ObjectProxy):
    id: str

    def __init__(self, source: Source, sid: str):
        super().__init__(source)
        self.id = sid


class Sources(t.Iterable[Source]):

    _sources: t.Mapping[str, SourceProxy]

    def __init__(self, sources: t.Mapping[str, Source]):
        self._sources = MappingProxyType({
            sid: SourceProxy(source, sid) for sid, source in sources.items()
        })

    def __getitem__(self, name: str):
        return self._sources.__getitem__(name)

    def __iter__(self):
        yield from self._sources.values()

    def items(self):
        return self._sources.items()

    def keys(self):
        return self._sources.keys()

    def __contains__(self, name: str):
        return name in self._sources


class BaseAuthenticator(Installable, Authenticator):

    sources: dict[str, Source]
    preflights: list[Preflight]

    def __init__(self,
                 sources: t.Mapping[str, Source] | None = None,
                 preflights: t.Iterable[Preflight] | None = None
                 ):
        self.sources = Sources(sources is not None and sources or {})
        self.preflights = preflights is not None and list(preflights) or []

    def install(self, application):
        application.services.register_value(Authenticator, self)
        application.services.register_factory(
            User,
            lambda svcs_container: self.identify(
                svcs_container.get(Request)
            )
        )

    def get_challenging_sources(self):
        for source_id, source in self.sources.items():
            if Challenge in source.actions:
                yield source_id, source

    def challenge(
            self, request: Request, credentials: dict
    ) -> tuple[str, User] | tuple[None, None]:
        for source_id, source in self.get_challenging_sources():
            action = source.get_action(Challenge, request)
            user = action.challenge(credentials)
            if user is not None:
                return source_id, user
        return None, None

    def identify(self, request) -> User | None:
        if self.preflights:
            logger.info(f'Authentication preflight found.')
            for resolver in self.preflights:
                if (user := resolver(request)) is not None:
                    logger.info(
                        f'Preflight user found by {resolver}: {user}.')
                    return user
            logger.info(f'Authentication preflight unsuccessful.')

        logger.info(f'Authentication initiated.')
        if (info := self.get_stored_info(request)) is not None:
            source = self.sources[info['source_id']]
            user = source.get(request, info['user_id'])
            if user is not None:
                logger.info(
                    f"Authentication by {info['source_id']} successful: {user}")
                return user

        return anonymous

    def get_stored_info(self, request) -> AuthenticationInfo:
        pass

    def forget(self, request) -> None:
        pass

    def remember(self, request, source_id: str, user: User) -> None:
        pass


@dataclass(kw_only=True)
class SessionAuthenticator(BaseAuthenticator):
    user_key: str

    def __init__(self, *, user_key,
                 sources: t.Mapping[str, Source] | None = None,
                 preflights: t.Iterable[Preflight] | None = None
                 ):
        self.user_key = user_key
        super().__init__(sources=sources, preflights=preflights)

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
