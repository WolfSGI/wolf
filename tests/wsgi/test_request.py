import pytest
from webtest.app import TestRequest as EnvironBuilder
from kettu.datastructures import Data
from kettu.headers import Query
from wolf.wsgi.request import Request


def test_request():
    environ = EnvironBuilder.blank('/?key=1', method='GET').environ
    request = Request(environ)
    assert request.path == '/'
    assert request.method == 'GET'
    assert request.body.read() == b''
    assert request.query == Query({'key': ('1',)})
    assert request.root_path == ''
    assert request.cookies is None
    assert request.content_type is None
    assert request.data == Data()
    assert request.application_uri == 'http://localhost'
    assert request.uri() == 'http://localhost/?key%3D1'
    assert request.uri(include_query=False) == 'http://localhost/'


def test_request_immutability():
    environ = EnvironBuilder.blank('/?key=1', method='GET').environ
    request = Request(environ)
    assert request.path == '/'

    with pytest.raises(AttributeError):
        request.path = '/test'

    del request.path
    request.environ['PATH_INFO'] = '/test'
    assert request.path == '/test'
