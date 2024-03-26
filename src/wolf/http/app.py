from abc import ABC, abstractmethod
from wolf.http.request import Request, E
from wolf.http.response import Response
from wolf.pluggability import Installable
from wolf.pipeline import HandlerWrapper
from aioinject import Container


class Application(ABC):

    services: Container
    middlewares: list[HandlerWrapper]

    def use(self, *components: Installable):
        for component in components:
            component.install(self)

    @abstractmethod
    def endpoint(self, request: Request) -> Response:
        ...

    @abstractmethod
    def resolve(self, environ: E) -> Response:
        ...
