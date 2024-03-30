from typing import NamedTuple, Any
from collections.abc import Sequence


class Data(NamedTuple):
    form: Sequence[tuple[str, Any]] | None = None
    json: int | float | str | dict | list | None = None  # not too specific
