import wrapt
import structlog
from typing import Sequence
from functools import partial
from wolf.rendering.ui import UI
from wolf.rendering.resources import Resource, NeededResources
from wolf.app.response import Response, FileWrapperResponse


logger = structlog.get_logger("wolf.app.render")


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
        ui = request.get(UI)
        needed_resources = request.get(NeededResources, default=None)
        if needed_resources is None:
            logger.warning("No resource injection.")
        else:
            if ui.resources:
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
