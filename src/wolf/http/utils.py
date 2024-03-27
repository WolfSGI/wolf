import typing as t
from collections.abc import Iterator, Sequence


# https://peps.python.org/pep-0594/
# Copied from CGI to avoid python 3.11 deprecating and python 3.13 removal
def _parseparam(s: str) -> Iterator[str]:
    while s[:1] == ";":
        s = s[1:]
        end = s.find(";")
        while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
            end = s.find(";", end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f.strip()
        s = s[end:]


def parse_header(line: str) -> tuple[str, dict[str, str]]:
    """Parse a Content-type like header.
    Return the main content-type and a dictionary of options.
    """
    parts = _parseparam(";" + line)
    key = parts.__next__()
    pdict = {}
    for p in parts:
        i = p.find("=")
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i + 1 :].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace("\\\\", "\\").replace('\\"', '"')
            pdict[name] = value
    return key, pdict


def consolidate_ranges(ranges: Sequence[tuple[int, int]]):
    ranges = iter(sorted(ranges))
    current_start, current_stop = next(ranges)
    for start, stop in ranges:
        if start > current_stop + 1:
            # Gap between segments: output current segment and start a new one.
            yield current_start, current_stop
            current_start, current_stop = start, stop
        else:
            # Segments adjacent or overlapping: merge.
            current_stop = max(current_stop, stop)
    yield current_start, current_stop
