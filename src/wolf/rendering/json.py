import wrapt
from wolf.wsgi.response import Response


@wrapt.decorator
def json(wrapped, instance, args, kwargs) -> Response:
    request = args[0]
    content = wrapped(*args, **kwargs)

    if isinstance(content, Response):
        return content

    if not isinstance(content, (dict, list)):
        raise TypeError(f"Unable to render type: {type(content)}.")

    return request.response_cls.to_json(body=content)
