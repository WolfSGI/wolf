class ETag(str):
    weak: bool = False

    def __new__(cls, value: str) -> 'ETag':
        weak = False
        if value.startswith(('W/', 'w/')):
            weak = True
            value = value[2:]

        # Etag value SHOULD be quoted.
        instance = super().__new__(cls, value.strip('"'))
        instance.weak = weak
        return instance

    def compare(self, other: 'ETag') -> bool:
        return self.value == other.value and not (self.weak or other.weak)

    def as_header(self) -> str:
        if self.weak:
            return f'W/"{self}"'
        return f'"{self}"'


class ETags(frozenset[ETag]):
    # IfMatch / IfMatchNone

    def as_header(self) -> str:
        return ','.join((etag.as_header() for etag in self))

    @classmethod
    def from_string(cls, header: str) -> frozenset[ETag]:
        if ',' not in header:
            header = header.strip()
            if header:
                etag = ETag(header)
                return cls((etag,))

        etags = []
        values = header.split(',')
        for value in values:
            value = value.strip()
            if value:
                etag = ETag(value)
                etags.append(etag)
        if not etags:
            raise ValueError()
        return cls(etags)
