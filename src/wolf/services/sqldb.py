from orjson import loads, dumps
from contextlib import contextmanager
from dataclasses import dataclass
from aioinject import Scoped
from beartype import beartype
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.engine.base import Engine
from wolf.pluggability import Installable


@beartype
@dataclass(kw_only=True)
class SQLDatabase(Installable):
    url: str
    echo: bool = False
    models_registries: tuple[type[SQLModel], ...] = (SQLModel,)

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
