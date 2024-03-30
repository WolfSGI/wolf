from typing import NamedTuple, Any
from collections.abc import Sequence


class Data(NamedTuple):
    form: Sequence[tuple[str, Any]] | None = None
    json: int | float | str | dict | list | None = None  # not too specific



class ETag(str):
    __slots__ = ('weak',)

    weak: bool

    def __new__(cls, value: str):
        if isinstance(value, ETag):
            return value

        weak = False
        if value.startswith(('W/', 'w/')):
            weak = True
            value = value[2:]

        # Etag value needs to be quoted.
        instance = super().__new__(cls, value[1:-1])
        instance.weak = weak
        return instance

    def compare(self, other: 'ETag') -> bool:
        return self == other and not (self.weak or other.weak)

    def as_header(self) -> str:
        if self.weak:
            return f'W/"{self}"'
        return f'"{self}"'
