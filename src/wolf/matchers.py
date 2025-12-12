import fnmatch
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description


class match_wildcards(BaseMatcher):

    def __init__(self, value: str):
        self.value: str = value

    def describe_to(self, description: Description):
        description.append_text(
            'String matching a wilcards string '
        ).append_text(self.value)

    def _matches(self, other: str):
        return fnmatch.fnmatch(other, self.value)
