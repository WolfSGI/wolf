import urllib.parse
from typing import NamedTuple, Any, Literal, TypeVar, Generic
from collections.abc import Mapping, Sequence
from biscuits import Cookie, parse
from frozendict import frozendict
from wolf.http.types import MIMEType
from wolf.http.exceptions import HTTPError
from wolf.http.utils import parse_header, consolidate_ranges


W = TypeVar('W', bound=str)


class Data(NamedTuple):
    form: Sequence[tuple[str, Any]] | None = None
    json: int | float | str | dict | list | None = None  # not too specific


class Range(NamedTuple):
    unit: str
    values: tuple[tuple[int, int], ...]

    def resolve(self, size: int) -> 'Range':
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
        return self._replace(values=tuple(consolidate_ranges(ranges)))

    @classmethod
    def from_string(cls, value: str | bytes) -> "Range":
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


class Weighted:

    exact: bool
    options: Mapping[str, str]

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Weighted):
            # When q values are equal, compare specificity instead:
            q = self.options.get('q', 1)
            qo = other.options.get('q', 1)
            if q == qo:
                return self.exact and not other.exact
            # Compare q values:
            return q < qo
        raise TypeError()


class Language(Weighted, str):
    __slots__ = ("locale", "options", "exact")

    locale: str

    def __new__(cls, value: str):
        if isinstance(value, cls):
            return value

        locale, params = parse_header(value)
        instance = str.__new__(
            cls, locale + "".join(
                f"; {k}={v}" for k, v in sorted(params.items())
            )
        )
        instance.locale = locale
        instance.exact = locale != '*'
        instance.options = frozendict(params)
        return instance

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.locale == other
        return False  # pragma: no cover


class ContentType(Weighted, str):
    __slots__ = ("mimetype", "options", "exact")

    mimetype: MIMEType

    def __new__(cls, value: str):
        if isinstance(value, cls):
            return value

        mimetype, params = parse_header(value)
        instance = str.__new__(
            cls, mimetype + "".join(
                f"; {k}={v}" for k, v in sorted(params.items())
            )
        )
        instance.mimetype = mimetype
        instance.exact = True
        instance.options = frozendict(params)
        return instance

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.mimetype == other
        return False  # pragma: no cover


class MediaType(ContentType):
    __slots__ = ("value", "options", "exact", "maintype", "subtype")

    maintype: str
    subtype: str | None

    def __new__(cls, value: str):
        if isinstance(value, cls):
            return value

        mimetype, params = parse_header(value)

        if mimetype == "*":
            maintype = "*"
            subtype = "*"
        elif "/" in mimetype:
            maintype, _, subtype = mimetype.partition("/")
        else:
            maintype = mimetype
            subtype = None

        instance = str.__new__(
            cls, mimetype + "".join(
                f"; {k}={v}" for k, v in sorted(params.items()))
        )
        instance.mimetype = mimetype
        instance.exact = "*" in mimetype
        instance.maintype = maintype
        instance.subtype = subtype
        instance.options = frozendict(params)
        return instance

    def match(self, other: str) -> bool:
        other_media_type = MediaType(other)  # idempotent
        return (
            self.maintype in {"*", other_media_type.maintype}
            and self.subtype in {"*", other_media_type.subtype}
        )


class Cookies(dict[str, Cookie]):
    """A Cookies management class, built on top of biscuits."""

    def set(self, name: str, *args, **kwargs):
        self[name] = Cookie(name, *args, **kwargs)

    @staticmethod
    def from_string(value: str) -> "Cookies":
        return parse(value)


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
