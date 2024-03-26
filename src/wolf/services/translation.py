import logging
from dataclasses import dataclass
from annotated_types import Len
from wolf.http.request import Request
from typing import NewType, List, Annotated
from aioinject import Scoped, Singleton
from wolf.pluggability import Installable
from vernacular import Translations
from vernacular.translate import Translator
from content_negotiation import decide_language, NoAgreeableLanguageError


logger = logging.getLogger(__name__)


Locale = NewType('Locale', str)


@dataclass(kw_only=True)
class TranslationService(Installable):
    translations: Translations
    accepted_languages: Annotated[List[str], Len(min_length=1)]
    default_domain: str = 'default'

    def install(self, application):
        application.services.register(Singleton(self.translator_factory))
        application.services.register(Scoped(self.locale_factory))

    def locale_factory(self, request: Request) -> Locale:
        header = request.environ.get('HTTP_ACCEPT_LANGUAGE')
        if header:
            try:
                language = decide_language(header.split(','), self.accepted_languages)
                logger.debug(f'Agreeing on requested language: {language}.')
                return Locale(language)
            except NoAgreeableLanguageError:
                # Fallback to default.
                logger.debug('Could not find a suitable language. Using fallback.')

        logger.debug('No language preference: Using fallback.')
        return Locale(self.accepted_languages[0])

    def translator_factory(self) -> Translator:
        return Translator(
            self.translations,
            self.default_domain,
            self.accepted_languages[0]
        )
