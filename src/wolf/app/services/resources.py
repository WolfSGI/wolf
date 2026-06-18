from pathlib import PurePosixPath
from html_resources.store import Repository
from wolf.app.nodes import Node
from wolf.app.render.html import BoundResources
from wolf.app.response import Response, FileWrapperResponse
from wolf.app.pluggability import Installable


class ResourceManager(Installable, Node):

    def __init__(self, repository: Repository, path: str | PurePosixPath):
        self.repository = repository
        self.path = PurePosixPath(path)

    def install(self, application):
        application.sinks[self.path] = self
        application.services.register_factory(
            BoundResources, self.needed_resources
        )

    def needed_resources(self):
        return BoundResources(self.path)

    def resolve(self, environ):
        info = self.repository.match(
            PurePosixPath(environ["PATH_INFO"].lstrip('/'))
        )
        if not info:
            return Response(status=404)

        headers = {
            "Content-Length": str(info.size),
            "Content-Type": info.content_type,
        }
        if environ["REQUEST_METHOD"] == "HEAD":
            return Response(200, headers=headers)

        return FileWrapperResponse(info.filepath, headers=headers)
