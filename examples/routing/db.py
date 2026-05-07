from authsources.identity import User
from authsources.protocols import Getter, Challenge
from authsources.source import Source, SourceAction
from sqlalchemy import select
from wolf.app.request import Request
from wolf.json import JSONSchema
from wolf_sql import Session

from models import Person


class Login(SourceAction):

    __protocols__ = (Challenge,)

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
        username = credentials.get('username')
        password = credentials.get('password')
        sqlsession = self.source.bindings['request'].get(Session)
        p = sqlsession.exec(
            select(Person).where(
                Person.email == username,
                Person.password == password
            )
        ).scalar_one_or_none()
        return p


class Fetch(SourceAction):

    __protocols__ = (Getter,)

    schema = None

    def get(self, uid: int) -> User | None:
        sqlsession = self.source.bindings['request'].get(Session)
        return sqlsession.get(Person, uid)


class DBSource(Source):
    pass
