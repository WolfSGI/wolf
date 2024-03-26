from http import HTTPStatus


REDIRECT_STATUSES = frozenset(
    (
        HTTPStatus.MULTIPLE_CHOICES,
        HTTPStatus.MOVED_PERMANENTLY,
        HTTPStatus.FOUND,
        HTTPStatus.SEE_OTHER,
        HTTPStatus.NOT_MODIFIED,
        HTTPStatus.USE_PROXY,
        HTTPStatus.TEMPORARY_REDIRECT,
        HTTPStatus.PERMANENT_REDIRECT,
    )
)

EMPTY_STATUSES = frozenset(
    (
        HTTPStatus.CONTINUE,
        HTTPStatus.SWITCHING_PROTOCOLS,
        HTTPStatus.PROCESSING,
        HTTPStatus.NO_CONTENT,
        HTTPStatus.NOT_MODIFIED,
    )
)
