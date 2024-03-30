from datetime import datetime, timezone, timedelta
from wolf.http.headers.utils import (
    parse_http_datetime, serialize_http_datetime
)


def test_http_datetime():
    strdt = "Wed, 21 Oct 2015 07:28:00 GMT"
    assert parse_http_datetime(strdt) == datetime(
        2015, 10, 21, 7, 28, tzinfo=timezone.utc
    )

    strdt = "Monday, 06-Nov-06 09:19:47 GMT"
    assert parse_http_datetime(strdt) == datetime(
        2006, 11, 6, 9, 19, 47,tzinfo=timezone.utc
    )


def test_dumps_datetime_as_http():
    tz = timezone(timedelta(hours=2), name="CET")
    dt = datetime(2015, 10, 21, 7, 28, tzinfo=tz)
    assert serialize_http_datetime(dt) == "Wed, 21 Oct 2015 05:28:00 GMT"
