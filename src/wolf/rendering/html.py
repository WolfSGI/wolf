import wrapt
import logging
from typing import Sequence
from functools import partial
from kettu.resources import Resource, NeededResources
from wolf.wsgi.response import WSGIResponse
from wolf.ui import UI


logger = logging.getLogger(__name__)


def html(func=None, *, resources: Sequence[Resource] | None = None):
    @wrapt.decorator
    def html_wrapper(wrapped, instance, args, kwargs) -> WSGIResponse:
        content = wrapped(*args, **kwargs)

        if isinstance(content, WSGIResponse):
            return content

        if not isinstance(content, str):
            raise TypeError(f"Unable to render type: {type(content)}.")

        request = args[0]
        ui = request.get(UI)
        needed_resources = request.get(NeededResources, default=None)
        if needed_resources is None:
            logger.debug("No resource injection.")
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
