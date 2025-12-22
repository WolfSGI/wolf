import structlog
from dataclasses import dataclass
from annotated_types import Len
from typing import NewType, Annotated
from vernacular import Translations
from vernacular.translate import Translator
from wolf.app.request import Request
from wolf.app.pluggability import Installable


logger = structlog.get_logger("wolf.app.services.translation")

Locale = NewType("Locale", str)


@dataclass(kw_only=True)
class TranslationService(Installable):
    translations: Translations
    accepted_languages: Annotated[list[str], Len(min_length=1)]
    default_domain: str = "default"

    def install(self, application):
        application.services.register_value(Translations, self.translations)
        application.services.register_factory(
            Translator,
            lambda svcs_container: self.translator_factory(
                svcs_container.get(Locale)
            )
        )
        application.services.register_factory(
            Locale,
            lambda svcs_container: self.locale_factory(
                svcs_container.get(Request)
            )
        )

    def translator_factory(self, locale: Locale) -> Translator:
        if locale is None:
            # fallback
            locale = Locale(self.accepted_languages[0])
            logger.warn(f'locale was not found. Using Fallback: {locale}.')
        return Translator(
            self.translations,
            self.default_domain,
            locale
        )

    def locale_factory(self, request: Request) -> Locale:
        language = request.accept_language.negotiate(
            self.accepted_languages
        )
        return Locale(language)
