import wrapt
import structlog
from pathlib import PurePosixPath
from typing import Sequence
from functools import partial
from wolf.rendering.ui import UI
from wolf.app.response import Response, FileWrapperResponse
from html_resources.resources import Resource
from html_resources.needed import NeededResources


logger = structlog.get_logger("wolf.app.render")


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


def html(func=None, *, resources: Sequence[Resource] | None = None):
    @wrapt.decorator
    def html_wrapper(
            wrapped, instance, args, kwargs
    ) -> Response | FileWrapperResponse:
        content = wrapped(*args, **kwargs)

        if isinstance(content, (Response, FileWrapperResponse)):
            return content

        if not isinstance(content, str):
            raise TypeError(f"Unable to render type: {type(content)}.")

        request = args[0]
        needed_resources = request.get(BoundResources, default=None)
        if needed_resources is None:
            logger.warning("No resource injection.")
        else:
            ui = request.get(UI, default=None)
            if ui is not None and ui.resources:
                needed_resources.precede(ui.resources)
            if resources:
                needed_resources.update(resources)
            content = needed_resources.apply(
                content,
                request.application_uri
            )

        return request.response_cls.html(body=content)

    if func is None:
        return partial(html, resources=resources)

    return html_wrapper(func)
