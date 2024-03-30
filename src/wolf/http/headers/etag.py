from typing import NamedTuple


class ETag(NamedTuple):
    value: str
    weak: bool = False

    @classmethod
    def from_string(cls, value: str) -> 'ETag':
        weak = False
        if value.startswith(('W/', 'w/')):
            weak = True
            value = value[2:]

        # Etag value needs to be quoted.
        return cls(value[1:-1], weak=weak)

    def compare(self, other: 'ETag') -> bool:
        return self.value == other.value and not (self.weak or other.weak)

    def as_header(self) -> str:
        if self.weak:
            return f'W/"{self.value}"'
        return f'"{self.value}"'


class IfMatch(tuple[Etag, ...]):
    # Please implement the "compare"

    def as_header(self) -> str:
        return ','.join((etag.as_header() for etag in self))

    @classmethod
    def from_string(cls, header: str) -> tuple[Etag, ...]:
        if ',' not in header:
            header = header.strip()
            if header:
                etag = Etag.from_string(header)
                return cls((etag,))

        etags = []
        values = header.split(',')
        for value in values:
            value = value.strip()
            if value:
                etag = ETag.from_string(value)
                etags.append(etag)
        if not etags:
            raise ValueError()
        return cls(langs)


class IfMatchNone(IfMatch):
    # Please implement the "compare"
    pass
