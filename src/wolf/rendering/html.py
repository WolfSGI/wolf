import inspect
import wrapt
import logging
from typing import Sequence
from functools import partial
from wolf.http.response import Response
from wolf.ui import UI
from wolf.resources import Resource, NeededResources


logger = logging.getLogger(__name__)


def html(wrapped=None, *,
         resources: Sequence[Resource] | None = None):

    @wrapt.decorator
    def html_wrapper(wrapped, instance, args, kwargs) -> Response:
        content = wrapped(*args, **kwargs)

        if isinstance(content, Response):
            return content

        if not isinstance(content, str):
            raise TypeError(
                f'Unable to render type: {type(content)}.')

        request = args[0]
        ui = request.get(UI)
        needed_resources = request.get(NeededResources, default=None)
        if needed_resources is None:
            logger.debug('No resource injection.')
        else:
            if ui.resources:
                needed_resources.update(ui.resources)
            if resources:
                needed_resources.update(resources)
            content = needed_resources.apply(
                content, request.application_uri
            )

        return request.response_cls.html(body=content)

    if wrapped is None:
        return partial(html, resources=resources)

    return html_wrapper(wrapped)
