import re
import urllib.parse
from enum import Enum
from fnmatch import fnmatch
from typing import Sequence, Literal, Mapping, Any, Union, NamedTuple
from biscuits import Cookie, parse
from frozendict import frozendict
from vernacular.utils import parse_locale
from wolf.http.exceptions import HTTPError
from wolf.http.types import MIMEType
from wolf.http.utils import parse_header, consolidate_ranges


WEIGHT = re.compile(r"^(0\.[0-9]{1,3}|1\.0{1,3})$")  # 3 decimals.
WEIGHT_PARAM = re.compile(r"^q=(0\.[0-9]{1,3}|1\.0{1,3})$")


class Specificity(int, Enum):
    NONSPECIFIC = 0
    PARTIALLY_SPECIFIC = 1
    SPECIFIC = 2


class Authorization(NamedTuple):
    scheme: str
    credentials: str

    @classmethod
    def from_string(cls, value: str):
        scheme, _, credentials = value.strip(' ').partition(' ')
        return cls(scheme.lower(), credentials.strip())


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


class Cookies(dict[str, Cookie]):
    """A Cookies management class, built on top of biscuits."""

    def set(self, name: str, *args, **kwargs):
        self[name] = Cookie(name, *args, **kwargs)

    @staticmethod
    def from_string(value: str) -> "Cookies":
        return parse(value)


class ContentType:
    __slots__ = ("mimetype", "options")

    quality: float
    formatted: str
    mimetype: MIMEType
    options: Mapping[str, str]

    def __init__(
            self,
            mimetype: MIMEType,
            options: Mapping[str, str],
    ):
        self.mimetype = mimetype
        self.options = options

    @classmethod
    def from_string(cls, value: str):
        mimetype, params = parse_header(value)
        return cls(
            mimetype=mimetype,
            options=frozendict(params)
        )

    def as_header(self):
        return self.mimetype + "".join(
            f";{k}={v}" for k, v in sorted(self.options.items())
        )

    def __bool__(self):
        return bool(self.mimetype)

    def __str__(self):
        return self.formatted

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ContentType):
            return (
                self.mimetype == other.mimetype and
                self.options == self.options
            )
        if isinstance(other, str):
            return self.mimetype == other
        return False


class MediaType(ContentType):
    __slots__ = (
        "options", "specificity", "maintype", "subtype", "quality")

    maintype: str
    subtype: str
    specificity: Specificity

    def __init__(
            self,
            maintype: str,
            subtype: str,
            options: Mapping[str, str],
            quality: float = 1.0,
    ):
        mimetype = maintype + '/' + subtype
        self.quality = quality
        self.maintype = maintype
        self.subtype = subtype

        if maintype == "*" and subtype == "*":
            self.specificity = Specificity.NONSPECIFIC
        elif subtype == "*":
            self.specificity = Specificity.PARTIALLY_SPECIFIC
        else:
            self.specificity = Specificity.SPECIFIC
        super().__init__(mimetype, options)

    @classmethod
    def from_string(cls, value: str):
        mimetype, params = parse_header(value)
        if mimetype == "*":
            maintype = "*"
            subtype = "*"
        elif "/" in mimetype:
            maintype, _, subtype = mimetype.partition("/")
            if not subtype:
                subtype  = "*"
            elif maintype == '*' and subtype != '*':
                raise ValueError()
        else:
            maintype = mimetype
            subtype = "*"

        params = frozendict(params)
        if 'q' in params:
            q = params['q']
            if not WEIGHT.match(q):
                raise ValueError()
            quality = float(q)
        else:
            quality = 1.0
        return cls(
            maintype=maintype,
            subtype=subtype,
            options=params,
            quality=quality
        )

    def as_header(self):
        return self.mimetype + "".join(
            f";{k}={v}" for k, v in sorted(self.options.items())
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.mimetype == other
        if isinstance(other, ContentType):
            return self.mimetype == self.mimetype

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, MediaType):
            if self.quality == other.quality:
                return self.specificity > other.specificity
            return self.quality > other.quality
        raise TypeError()

    def match(self, other: str | ContentType) -> bool:
        if isinstance(other, ContentType):
            other = other.mimetype
        if self.specificity == Specificity.NONSPECIFIC:
            return True
        if self.specificity == Specificity.PARTIALLY_SPECIFIC:
            return fnmatch(other, self.mimetype)
        return self.mimetype == other


class Accept(tuple[MediaType, ...]):

    def __new__(cls, values: Sequence[MediaType]):
        return super().__new__(cls, sorted(values))

    def as_header(self):
        return ','.join((media.as_header() for media in self))

    @classmethod
    def from_string(cls, header: str, keep_null: bool = False):
        if ',' not in header:
            header = header.strip()
            if header:
                media = MediaType.from_string(header)
                if not keep_null and not media.quality:
                    raise ValueError()
                return cls((media,))

        medias = []
        values = header.split(',')
        for value in values:
            value = value.strip()
            if value:
                media = MediaType.from_string(value)
                if not keep_null and not media.quality:
                    continue
                medias.append(media)
        if not medias:
            raise ValueError()
        return cls(medias)

    def negotiate(self, supported: Sequence[str | MediaType]):
        if not self:
            if not supported:
                return None
            return supported[0]
        for accepted in self:
            for candidate in supported:
                if accepted.match(candidate):
                    return candidate
        return None


class Language:
    __slots__ = ("language", "variant", "quality", "specificity")

    language: str
    variant: str | None
    quality: float
    specificity: Specificity

    def __init__(
            self,
            locale: str,
            quality: float = 1.0
    ):
        if locale == '*':
            self.language = "*"
            self.variant = None
            self.specificity = Specificity.NONSPECIFIC
        else:
            self.language, self.variant = parse_locale(locale)
            self.specificity = (
                Specificity.SPECIFIC if self.variant
                else Specificity.PARTIALLY_SPECIFIC
            )
        self.quality = quality

    @classmethod
    def from_string(cls, value: str) -> 'Language':
        locale, _, rest = value.partition(';')
        rest = rest.strip()
        if rest:
            matched = WEIGHT_PARAM.match(rest)
            if not matched:
                raise ValueError()
            quality = float(matched.group(1))
            return cls(locale.strip(), quality)
        return cls(locale.strip())

    def __str__(self):
        if not self.variant:
            return self.language
        return f'{self.language}-{self.variant}'

    def as_header(self):
        return f"{str(self)};q={self.quality}"

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Language):
            if self.quality == other.quality:
                return self.specificity > other.specificity
            return self.quality > other.quality
        raise TypeError()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Language):
            return (
                self.language == other.language
                and self.variant == other.variant
            )
        if isinstance(other, str):
            return str(self) == other
        return False

    def match(self, other: Union[str, 'Language']) -> bool:
        if self.specificity == Specificity.NONSPECIFIC:
            return True

        if isinstance(other, str):
            language, variant = parse_locale(other)
        else:
            language = other.language
            variant = other.variant

        if self.specificity == Specificity.PARTIALLY_SPECIFIC or not variant:
            return language == self.language

        return (language == self.language and variant == self.variant)


class Languages(tuple[Language, ...]):

    def __new__(cls, values: Sequence[Language]):
        return super().__new__(cls, sorted(values))

    def as_header(self):
        return ','.join((lang.as_header() for lang in self))

    @classmethod
    def from_string(cls, header: str, keep_null: bool = False):
        if ',' not in header:
            header = header.strip()
            if header:
                lang = Language.from_string(header)
                if not keep_null and not lang.quality:
                    raise ValueError()
                return cls((lang,))

        langs = []
        values = header.split(',')
        for value in values:
            value = value.strip()
            if value:
                lang = Language.from_string(value)
                if not keep_null and not lang.quality:
                    continue
                langs.append(lang)
        if not langs:
            raise ValueError()
        return cls(langs)

    def negotiate(self, supported: Sequence[str | Language]):
        if not self:
            if not supported:
                return None
            return supported[0]
        for accepted in self:
            for candidate in supported:
                if accepted.match(candidate):
                    return candidate
        return None


class Range(NamedTuple):
    unit: str
    values: tuple[tuple[int, int], ...]

    def resolve(self, size: int, merge: bool = False) -> 'Range':
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
