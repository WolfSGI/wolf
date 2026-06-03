from pathlib import PurePosixPath
from wolf.app.nodes import Node
from wolf.app.response import Response, FileWrapperResponse
from htm_resources.needed import NeededResources as Resources
from htm_resources.store import Repository
from wolf.app.pluggability import Installable


class BoundResources(NeededResources):

    def __init__(self, path: str | PurePosixPath, *args, **kwargs):
        self.path = PurePosixPath(path)
        super().__init__(*args, **kwargs)

    def apply(self, body: str | bytes, base_uri: str = "") -> bytes:
        if len(self.data) == 0:
            return body

        if isinstance(body, str):
            body = body.encode()

        top = b""
        bottom = b""
        for resource in self.unfold():
            if resource.bottom:
                bottom += resource.render(base_uri / self.path)
            else:
                top += resource.render(base_uri / self.path)
        if top:
            body = body.replace(b"</head>", top + b"</head>", 1)
        if bottom:
            body = body.replace(b"</body>", bottom + b"</body>", 1)
        return body


class ResourcesManager(Installable, Node):

    def __init__(self, repository: Repository, path: str | PurePosixPath):
        self.repository = repository
        self.path = PurePosixPath(path)

    def install(self, application):
        application.sinks[self.path] = self
        application.services.register_factory(
            NeededResources, NeededResources()
        )

    def resolve(self, environ):
        info = self.match(environ["PATH_INFO"])
        if not info:
            return Response(status=404)

        headers = {
            "Content-Length": str(info["size"]),
            "Content-Type": info["content_type"],
        }
        if environ["REQUEST_METHOD"] == "HEAD":
            return Response(200, headers=headers)

        return FileWrapperResponse(info["filepath"], headers=headers)
