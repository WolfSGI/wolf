from uuid import uuid4
from typing import NamedTuple, Sequence
from wolf.http.exceptions import HTTPError


class Ranges(NamedTuple):
    unit: str
    values: tuple[tuple[int, int], ...]

    def resolve(self, size: int, merge: bool = False) -> 'Ranges':
        max_size = size - 1
        ranges = []
        for first, last in self.values:
            if first < 0:
                first = size + first
                if first < 0:
                    first = 0
            if last == -1:
                last = max_size
            elif last > max_size:
                last = max_size
            ranges.append((first, last))
        if merge:
            ranges = consolidate_ranges(ranges)
        return self._replace(values=tuple(ranges))

    @classmethod
    def from_string(cls, value: str | bytes) -> "Ranges":
        if '=' not in value:
            raise HTTPError(
                400,
                body="Missing range unit, e.g. 'bytes='")

        unit, _, values = value.partition('=')

        ranges = []
        for rg in values.split(','):
            first, dash, last = rg.strip().partition('-')
            try:
                if not dash:
                    raise ValueError("Range is malformed.")

                if first and last:
                    first, last = (int(first), int(last))
                    if last < first:
                        raise ValueError("Range is malformed.")
                elif first:
                    first, last = (int(first), -1)
                elif last:
                    first, last = (-int(last), -1)
                    if first >= 0:
                        raise ValueError()
                else:
                    raise ValueError("Range offsets are missing.'")
                ranges.append((first, last))
            except ValueError as exc:
                default_error = "Range is malformed."
                raise HTTPError(
                    400,
                    body=str(exc) or default_error)
        return cls(unit=unit, values=tuple(ranges))


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


def bytes_multipart(
        body: bytes | str,
        content_type: str,
        ranges: Ranges,
        max_size: int):
    boundary = yield
    chunks = ranges.resolve(max_size)
    yield f"--{boundary}\r\n"
    for first, last in chunks.values:
        yield f"Content-Type: {content_type}\r\n"
        yield f"Content-Range: bytes {first}-{last}/{max_size}\r\n\r\n"
        yield body[first:last]
        yield f"--{boundary}\r\n"
