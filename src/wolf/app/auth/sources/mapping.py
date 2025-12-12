from wolf.abc.auth import Source
from wolf.abc.source import Challenge
from wolf.json import JSONSchema
from signature_registries import TypedValue


class Login(Challenge):

    schema = JSONSchema({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Login",
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "User name."
            },
            "password": {
                "type": "string",
                "description": "User password"
            }
        },
        "required": ["username", "password"]
    })

    def challenge(self, credentials: dict) -> User | None:
        errors = list(self.schema.validate(credentials))
        if not errors:
            username = credentials.get("username")
            password = credentials.get("password")
            if username is not None and username in self.source.users:
                if self.source.users[username] == password:
                    user = User()
                    user.id = username
                    return user
        else:
            # FixMe
            return None


class DictSource(Source):

    actions = {
        Challenge: Login
    }

    def __init__(self, users: dict[str, str]):
        self.users = users

    def get(self, uid: UserID) -> User | None:
        if uid in self.users:
            user = User()
            user.id = uid
            return user
