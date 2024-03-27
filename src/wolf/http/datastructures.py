import urllib.parse
from typing import NamedTuple, Any, Literal
from collections.abc import Mapping, Sequence
from biscuits import Cookie, parse
from frozendict import frozendict
from wolf.http.types import MIMEType
from wolf.http.utils import parse_header


class Data(NamedTuple):
    form: Sequence[tuple[str, Any]] | None = None
    json: int | float | str | dict | list | None = None  # not too specific


class ContentType(str):
    __slots__ = ("mimetype", "options")

    mimetype: MIMEType
    options: Mapping[str, str]

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
        instance.options = frozendict(params)
        return instance


class MediaType(ContentType):
    __slots__ = ("options", "mimetype", "maintype", "subtype")

    mimetype: MIMEType
    maintype: str
    subtype: str | None
    options: Mapping[str, str]

    def __new__(cls, value: str):
        if isinstance(value, cls):
            return value

        mimetype, params = parse_header(value)

        if mimetype == "*":
            maintype = "*"
            subtype = "*"
        elif "/" in mimetype:
            type_parts = mimetype.split("/")
            if not type_parts or len(type_parts) > 2:
                raise ValueError(f"Can't parse mimetype {mimetype!r}")
            maintype, subtype = type_parts
        else:
            maintype = mimetype
            subtype = None

        instance = str.__new__(
            cls, mimetype + "".join(f"; {k}={v}" for k, v in sorted(params.items()))
        )

        instance.mimetype = mimetype
        instance.maintype = maintype
        instance.subtype = subtype
        instance.options = frozendict(params)
        return instance

    def match(self, other: str) -> bool:
        other_media_type = MediaType(other)  # idempotent
        return self.maintype in {"*", other_media_type.maintype} and self.subtype in {
            "*",
            other_media_type.subtype,
        }


class Cookies(dict[str, Cookie]):
    """A Cookies management class, built on top of biscuits."""

    def set(self, name: str, *args, **kwargs):
        self[name] = Cookie(name, *args, **kwargs)

    @staticmethod
    def from_string(value: str):
        return parse(value)


class Query(frozendict[str, Sequence[str]]):
    TRUE_STRINGS = {"t", "true", "yes", "1", "on"}
    FALSE_STRINGS = {"f", "false", "no", "0", "off"}
    NONE_STRINGS = {"n", "none", "null"}

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
    ):
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
