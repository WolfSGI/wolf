from orjson import loads, dumps
from typing import Tuple, Type
from contextlib import contextmanager
from dataclasses import dataclass
from aioinject import Scoped
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.engine.base import Engine
from wolf.pluggability import Installable


@dataclass(kw_only=True)
class SQLDatabase(Installable):
    url: str
    echo: bool = False
    models_registries: Tuple[Type[SQLModel], ...] = (SQLModel,)

    def __post_init__(self):
        engine: Engine = create_engine(
            self.url,
            echo=self.echo,
            json_serializer=dumps,
            json_deserializer=loads
        )
        for registry in self.models_registries:
            registry.metadata.create_all(engine)
        self.engine = engine

    def install(self, application):
        application.services.register(Scoped(self.sqlsession))

    @contextmanager
    def sqlsession(self) -> Session:
        with Session(self.engine) as session:
            try:
                yield session
            except Exception:
                # maybe log.
                raise
            else:
                session.commit()
