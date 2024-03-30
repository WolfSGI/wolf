from biscuits import Cookie, parse


class Cookies(dict[str, Cookie]):
    """A Cookies management class, built on top of biscuits."""

    def set(self, name: str, *args, **kwargs):
        self[name] = Cookie(name, *args, **kwargs)

    @staticmethod
    def from_string(value: str) -> "Cookies":
        return parse(value)
