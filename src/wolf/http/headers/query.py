import urllib.parse
from typing import Sequence, Literal

from frozendict import frozendict


class Query(frozendict[str, Sequence[str]]):
    TRUE_STRINGS: set[str] = frozenset(("t", "true", "yes", "1", "on"))
    FALSE_STRINGS: set[str] = frozenset(("f", "false", "no", "0", "off"))
    NONE_STRINGS: set[str] = frozenset(("n", "none", "null"))

    def get(self, name: str, default=None):
        """Return the first value of the found list."""
        return super().get(name, [None])[0]

    def getlist(self, name: str) -> Sequence[str]:
        """Return the value list"""
        return super().get(name, [])

    def as_bool(self, key: str) -> bool | None:
        value = self[key][0]
        value = value.lower()
        if value in self.TRUE_STRINGS:
            return True
        elif value in self.FALSE_STRINGS:
            return False
        elif value in self.NONE_STRINGS:
            return None
        raise ValueError(f"Can't cast {value!r} to boolean.")

    def as_int(self, key: str) -> int:
        return int(self[key][0])

    def as_float(self, key: str) -> float:
        return float(self[key][0])

    @classmethod
    def from_string(
        cls,
        value: str,
        keep_blank_values: bool = True,
        strict_parsing: bool = True,
        encoding: str = "utf-8",
        errors: Literal["strict", "replace", "ignore"] = "replace",
        max_num_fields: int = None,
        separator: str = "&",
    ) -> "Query":
        if not value:
            return cls()
        return cls(
            (key, tuple(val))
            for key, val in urllib.parse.parse_qs(
                value,
                keep_blank_values=keep_blank_values,
                strict_parsing=strict_parsing,
                encoding=encoding,
                errors=errors,
                max_num_fields=max_num_fields,
                separator=separator,
            ).items()
        )
