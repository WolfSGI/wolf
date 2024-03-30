import re
from datetime import datetime
from email.utils import parsedate_to_datetime


# Borrowed from Sanic
# CGI parse header is deprecated.
_token, _quoted = r"([\w!#$%&'*+\-.^_`|~]+)", r'"([^"]*)"'
_param = re.compile(rf";\s*{_token}=(?:{_token}|{_quoted})", re.ASCII)


def parse_header(value: str) -> tuple[str, dict[str, str]]:
    pos = value.find(";")
    if pos == -1:
        options = {}
    else:
        options = {
            m.group(1).lower(): (m.group(2) or m.group(3))
            .replace("%22", '"')
            .replace("%0D%0A", "\n")
            for m in _param.finditer(value[pos:])
        }
        value = value[:pos]
    return value.strip().lower(), options


parse_http_datetime = parsedate_to_datetime


def serialize_http_datetime(dt: datetime) -> str:
    """Returns an RFC 1123 datetime string
    """
    return dt.strftime('%a, %d %b %Y %H:%M:%S %Z')
