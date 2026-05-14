import pytest
from svcs import Registry
from webtest.app import TestRequest as EnvironBuilder
from kettu.datastructures import Data
from kettu.headers import Cookies, Query, Authorization, DigestAuthParams
from wolf.app.request import Request, ServiceNotFoundError
from wolf.app.response import Response


class MockService:
    pass


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


def test_request_authorization():
    environ = EnvironBuilder.blank(
        '/',
        authorization="Bearer Whatever"
    ).environ
    request = Request(environ)
    assert request.authorization == Authorization(
        scheme='bearer',
        credentials="Whatever"
    )

    environ = EnvironBuilder.blank(
        '/',
        authorization='Digest uri="/?a=b"'
    ).environ
    request = Request(environ)
    assert request.authorization == (
        'digest',
        DigestAuthParams(
            uri="/?a=b"
        )
    )


def test_request_response_class():
    environ = EnvironBuilder.blank('/', method='GET').environ
    request = Request(environ)
    assert request.response_cls is Response

    class MyResponse(Response):
        ...

    request = Request(environ, response_cls=MyResponse)
    assert request.response_cls is MyResponse


def test_blank_context():
    environ = EnvironBuilder.blank('/', method='GET').environ
    request = Request(environ)

    with pytest.raises(NotImplementedError):
        request.get(Cookies)

    context = Registry()
    with request(context):
        assert request.get(Cookies) is request.cookies
        assert request.get(Query) is request.query
        assert request.get(Request) is request

        data = request.get(Data)
        assert isinstance(data, Data)

        with pytest.raises(ServiceNotFoundError):
            assert request.get(MockService)

        assert request.get(MockService, default=None) is None
