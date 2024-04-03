from kettu.identity import Source, User
from wolf.wsgi.request import WSGIRequest
from sqlmodel import Session
from sqlalchemy import select
from models import Person


class DBSource(Source):

    def find(self, credentials: dict, request: WSGIRequest) -> User | None:
        username = credentials.get('username')
        password = credentials.get('password')
        sqlsession = request.get(Session)
        p = sqlsession.exec(
            select(Person).where(
                Person.email == username,
                Person.password == password
            )
        ).scalar_one_or_none()
        return p

    def fetch(self, uid, request) -> User | None:
        sqlsession = request.get(Session)
        return sqlsession.get(Person, uid)
