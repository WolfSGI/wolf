import pytest

from pathlib import Path, PosixPath
from svcs import Registry
from webtest.app import TestRequest as EnvironBuilder

from html_resources.library import Library
from wolf.app.render.html import html, BoundResources
from wolf.app.request import Request
from wolf.app.response import Response


HERE = Path(__file__).parent.resolve()
RESOURCES = HERE / "resources"


def test_html_render_response():
    environ = EnvironBuilder.blank('/').environ
    request = Request(environ)
    response = Response(200, body="Nothing to see.")

    @html
    def my_view(request):
        return response

    result = my_view(request)
    assert result is response
    assert result.headers == {}


def test_html_render_no_context():
    environ = EnvironBuilder.blank('/').environ
    request = Request(environ)

    @html
    def my_view(request):
        return "This is the content"

    with pytest.raises(NotImplementedError):
        my_view(request)


def test_html_render_empty_context():
    environ = EnvironBuilder.blank('/').environ
    request = Request(environ)

    @html
    def my_view(request):
        return "This is the content"

    context = Registry()
    with request(context):
        response = my_view(request)

    assert response.body == 'This is the content'
    assert response.headers == {'Content-Type': 'text/html;charset=utf-8'}


def test_html_render_resources():
    environ = EnvironBuilder.blank('/').environ
    request = Request(environ)

    store = Library.from_discovery("my_lib", RESOURCES)
    js_resource = store.bind('hello.js')
    css_resource = store.bind('example.css')

    @html(resources=[js_resource, css_resource])
    def my_view(request):
        return """
<html>
  <head></head>
  <body>This is the content</body>
</html>
"""

    context = Registry()
    resources = BoundResources(path="static")
    context.register_value(BoundResources, resources)

    with request(context):
        response = my_view(request)

    assert response.body == b'\n<html>\n  <head><script src="http:/localhost/static/my_lib/hello.js" integrity="sha256-yFZn6wscZfgJynmR6A9NFVN6HMNUwHhfE1TrMnJ2HPA="></script>\n<link rel="stylesheet" href="http:/localhost/static/my_lib/example.css" integrity="sha256-ogCX0ULq8M9SOMyenKNy8HjkPNfr9lNokjg7i09IUBs=" />\n</head>\n  <body>This is the content</body>\n</html>\n'
    assert response.headers == {'Content-Type': 'text/html;charset=utf-8'}
