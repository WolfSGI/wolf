from fnmatch import fnmatch
from typing import Mapping, Any, Sequence

from frozendict import frozendict

from wolf.http.headers.constants import WEIGHT, Specificity
from wolf.http.types import MIMEType
from wolf.http.headers.utils import parse_header


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
        if values:
            return super().__new__(cls, sorted(values))
        return super().__new__(cls, (MediaType('*', '*', {}),))

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
