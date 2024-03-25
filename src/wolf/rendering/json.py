import inspect
import wrapt
from wolf.http.response import Response


def json(wrapped):

    @wrapt.decorator
    def _sync_json(wrapped, instance, args, kwargs) -> Response:
        request = args[0]
        content = wrapped(*args, **kwargs)

        if isinstance(content, Response):
            return content

        if not isinstance(content, (dict, list)):
            raise TypeError(f'Unable to render type: {type(content)}.')

        return request.response_cls.to_json(body=content)

    return json_wrapper(wrapped)
