import inspect
import wrapt
from typing import Sequence
from functools import partial
from wolf.http.response import Response
from wolf.resources import Resource


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
        return request.response_cls.html(body=content)

    if wrapped is None:
        return partial(html, resources=resources)

    return html_wrapper(wrapped)
