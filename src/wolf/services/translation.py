import logging
from annotated_types import Len
from typing import NewType, List, Annotated
from winkel.plugins import ServiceManager, Configuration, factory
from vernacular import Translations
from vernacular.translate import Translator
from content_negotiation import decide_language, NoAgreeableLanguageError


logger = logging.getLogger(__name__)


Locale = NewType('Locale', str)


class TranslationService(ServiceManager, Configuration):
    translations: Translations
    accepted_languages: Annotated[List[str], Len(min_length=1)]
    default_domain: str = 'default'

    __provides__ = [Locale, Translator]

    @factory('scoped')
    def locale_factory(self, scope) -> Locale:
        header = scope.environ.get('HTTP_ACCEPT_LANGUAGE')
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


    @factory('singleton')
    def translator_factory(self, scope) -> Translator:
        return Translator(
            self.translations,
            self.default_domain,
            self.accepted_languages[0]
        )
