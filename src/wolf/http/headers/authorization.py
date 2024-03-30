from typing import NamedTuple


class Authorization(NamedTuple):
    scheme: str
    credentials: str

    @classmethod
    def from_string(cls, value: str):
        scheme, _, credentials = value.strip(' ').partition(' ')
        return cls(scheme.lower(), credentials.strip())
