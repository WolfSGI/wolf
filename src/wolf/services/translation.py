import logging
from dataclasses import dataclass
from annotated_types import Len
from typing import NewType, Annotated
from aioinject import Scoped, Singleton
from kettu.http.request import Request
from kettu.pluggability import Installable
from vernacular import Translations
from vernacular.translate import Translator


logger = logging.getLogger(__name__)

Locale = NewType("Locale", str)


@dataclass(kw_only=True)
class TranslationService(Installable):
    translations: Translations
    accepted_languages: Annotated[list[str], Len(min_length=1)]
    default_domain: str = "default"

    def install(self, application):
        application.services.register(Singleton(self.translator_factory))
        application.services.register(Scoped(self.locale_factory))

    def locale_factory(self, request: Request) -> Locale:
        language = request.accept_language.negotiate(
            self.accepted_languages
        )
        return Locale(language)

    def translator_factory(self) -> Translator:
        return Translator(
            self.translations,
            self.default_domain,
            self.accepted_languages[0]
        )
