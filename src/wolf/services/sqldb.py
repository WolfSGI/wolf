from orjson import loads, dumps
from typing import Tuple, Type
from functools import cached_property
from winkel.response import Response
from pydantic import computed_field
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.engine.base import Engine
from winkel.plugins import ServiceManager, Configuration, factory
from transaction import TransactionManager
from contextlib import contextmanager


class SQLDatabase(ServiceManager, Configuration):

    __provides__ = [Session]

    url: str
    echo: bool = False
    models_registries: Tuple[Type[SQLModel], ...] = (SQLModel,)

    @computed_field
    @cached_property
    def engine(self) -> Engine:
        engine = create_engine(
            self.url,
            echo=self.echo,
            json_serializer=dumps,
            json_deserializer=loads
        )
        for registry in self.models_registries:
            registry.metadata.create_all(engine)
        return engine

    @factory('scoped')
    def session_factory(self, scope) -> Session:
        return scope.stack.enter_context(self.sqlsession(scope))

    @contextmanager
    def sqlsession(self, scope):
        with Session(self.engine) as session:
            try:
                yield session
            except Exception:
                # maybe log.
                raise
            else:
                response = scope.get(Response)
                if response.status >= 400:
                    session.rollback()
                    return

                if TransactionManager in scope:
                    txn = scope.get(TransactionManager)
                    if txn.isDoomed():
                        session.rollback()
                        return

                session.commit()
