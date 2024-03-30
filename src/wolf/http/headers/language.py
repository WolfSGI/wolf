from typing import Any, Union, Sequence

from vernacular.utils import parse_locale

from wolf.http.headers.constants import WEIGHT_PARAM, Specificity


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
        if values:
            return super().__new__(cls, sorted(values))
        return super().__new__(cls, (Language('*'),))

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
