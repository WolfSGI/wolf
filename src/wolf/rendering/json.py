import wrapt
from wolf.wsgi.response import WSGIResponse


@wrapt.decorator
def json(wrapped, instance, args, kwargs) -> WSGIResponse:
    request = args[0]
    content = wrapped(*args, **kwargs)

    if isinstance(content, WSGIResponse):
        return content

    if not isinstance(content, (dict, list)):
        raise TypeError(f"Unable to render type: {type(content)}.")

    return request.response_cls.to_json(body=content)
