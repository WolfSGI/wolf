import pytest
from http import HTTPStatus
from wolf.http.exceptions import HTTPError


def test_exception():
    with pytest.raises(ValueError) as exc:
        HTTPError('abc')
    assert str(exc.value) == "'abc' is not a valid HTTPStatus"

    exc = HTTPError(400)
    assert exc.status == HTTPStatus(400)
    assert exc.body == b'Bad request syntax or unsupported method'

    exc = HTTPError(400, body='')
    assert exc.status == HTTPStatus(400)
    assert exc.body == b''

    exc = HTTPError(404, body='I did not find anything')
    assert exc.status == HTTPStatus(404)
    assert exc.body == b'I did not find anything'

    exc = HTTPError(404, body=b'Works with bytes body')
    assert exc.status == HTTPStatus(404)
    assert exc.body == b'Works with bytes body'

    with pytest.raises(ValueError) as exc:
        HTTPError(200, 200)
    assert str(exc.value) == "Body must be string or bytes."
