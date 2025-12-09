from wolf.abc.identity import User
from wolf.abc.auth import Source
from wolf.abc.source import Challenge
from wolf.json import JSONSchema
from wolf.wsgi.request import Request
from sqlmodel import Session
from sqlalchemy import select, func
from models import Person


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
        username = credentials.get('username')
        password = credentials.get('password')
        sqlsession = self.request.get(Session)
        p = sqlsession.exec(
            select(Person).where(
                Person.email == username,
                Person.password == password
            )
        ).scalar_one_or_none()
        return p


class DBSource(Source):

    actions = {
        Challenge: Login
    }

    def get(self, request: Request, uid) -> User | None:
        sqlsession = request.get(Session)
        return sqlsession.get(Person, uid)
