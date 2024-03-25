from winkel.auth import Source, User
from winkel.scope import Scope
from sqlmodel import Session
from sqlalchemy import select
from models import Person


class DBSource(Source):

    def find(self, credentials: dict, scope: Scope) -> User | None:
        username = credentials.get('username')
        password = credentials.get('password')
        sqlsession = scope.get(Session)
        p = sqlsession.exec(
            select(Person).where(
                Person.email == username,
                Person.password == password
            )
        ).scalar_one_or_none()
        return p

    def fetch(self, uid, scope) -> User | None:
        sqlsession = scope.get(Session)
        return sqlsession.get(Person, uid)