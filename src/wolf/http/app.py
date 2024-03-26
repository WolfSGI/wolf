from abc import ABC, abstractmethod
from wolf.http.request import Request
from wolf.http.response import Response, FileResponse
from wolf.pluggability import Installable
from wolf.pipeline import Wrapper
from aioinject import Container


class Application(ABC):

    services: Container
    middlewares: tuple[Wrapper]

    def use(self, *components: Installable):
        for component in components:
            component.install(self)

    @abstractmethod
    def endpoint(self, request: Request) -> Response | FileResponse:
        ...
